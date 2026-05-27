"""Compare parsed command profiles through the existing evaluation framework."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from combatrl.evaluation.benchmark_suite import BenchmarkSuite
from combatrl.evaluation.reports import write_comparison_report
from combatrl.nlp.parser import parse_command_to_profile
from combatrl.nlp.validation import sanitize_profile_id
from combatrl.profiles.loader import load_profile_by_id
from combatrl.replay.validators import validate_replay
from combatrl.schemas.configs import load_environment_config, load_simulation_config
from combatrl.schemas.evaluation import PolicySpec, ScenarioSpec
from combatrl.schemas.nlp import BehaviorProfileParseResult
from combatrl.schemas.profiles import BehaviorProfile

DEFAULT_SCENARIO = Path("configs/env/gym_2v2_controlled_ranged.yaml")
SUMMARY_FIELDS = (
    "command",
    "profile_id",
    "success",
    "attack_action_rate",
    "retreat_action_rate",
    "avg_distance_to_ally",
    "avg_distance_to_nearest_enemy",
    "win_rate",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare profiles generated from commands.")
    parser.add_argument("--commands", nargs="+", required=True)
    parser.add_argument("--base-profile", default="balanced")
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--base-policy", default="aggressive")
    parser.add_argument("--opponent-policy", default="aggressive")
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--num-seeds", type=int, default=10)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/metrics/command_profiles"),
    )
    parser.add_argument("--controlled-agent", default=None)
    parser.add_argument("--replay-sample-count", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.num_seeds <= 0:
        print("compare_command_profiles failed: --num-seeds must be positive", file=sys.stderr)
        return 1
    try:
        base_profile = load_profile_by_id(args.base_profile)
        scenario_spec = _build_scenario_spec(args)
    except Exception as exc:
        print(f"compare_command_profiles failed: {exc}", file=sys.stderr)
        return 1

    seeds = list(range(args.seed_start, args.seed_start + args.num_seeds))
    run_id = datetime.now(UTC).strftime("run_%H%M%S")
    output_dir = args.output_dir / run_id
    parsed_dir = output_dir / "parsed_profiles"
    parsed_dir.mkdir(parents=True, exist_ok=True)

    suite = BenchmarkSuite(output_dir=output_dir / "evals")
    results = []
    rows: list[dict[str, object]] = []
    parse_results: list[BehaviorProfileParseResult] = []
    sample_replay_paths: dict[str, list[str]] = {}

    for index, command in enumerate(args.commands):
        parse_result = parse_command_to_profile(command, base_profile=base_profile)
        parse_results.append(parse_result)
        parse_path = parsed_dir / f"{index:02d}_{sanitize_profile_id(command)}_parse.json"
        parse_path.write_text(
            json.dumps(parse_result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if not parse_result.success or parse_result.profile is None:
            rows.append(_failed_row(command, parse_result))
            continue

        profile_path = parsed_dir / f"{index:02d}_{sanitize_profile_id(command)}.yaml"
        _write_profile(profile_path, parse_result.profile)
        evaluation_profile_id = f"cmd{index:02d}"
        policy_spec = PolicySpec(
            policy_id=f"profiled:{args.base_policy}:{evaluation_profile_id}",
            policy_type="profiled",
            base_policy_id=args.base_policy,
            profile_id=evaluation_profile_id,
            profile_path=str(profile_path),
            controlled_agent_id=scenario_spec.controlled_agent_id,
        )
        result = suite.run(
            scenario_spec=scenario_spec,
            policy_spec=policy_spec,
            seeds=seeds,
            save_replays=args.save_replays,
            replay_sample_count=args.replay_sample_count,
        )
        results.append(result)
        for replay_path in result.replay_sample_paths:
            validate_replay(replay_path)
        sample_replay_paths[command] = result.replay_sample_paths
        rows.append(_row_from_result(command, parse_result.profile, result.aggregate_metrics))

    comparison_paths = (
        write_comparison_report(results, output_dir / "comparison_report") if results else {}
    )
    summary_json_path = output_dir / "command_profile_summary.json"
    summary_csv_path = output_dir / "command_profile_summary.csv"
    payload = {
        "metrics_schema_version": "1.0",
        "scenario": str(args.scenario),
        "base_profile": args.base_profile,
        "base_policy": args.base_policy,
        "seeds": seeds,
        "rows": rows,
        "parse_results": [result.model_dump(mode="json") for result in parse_results],
        "sample_replay_paths": sample_replay_paths,
        "comparison_report_paths": {key: str(value) for key, value in comparison_paths.items()},
    }
    summary_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(summary_csv_path, rows)

    print(f"summary_json_path: {summary_json_path}")
    print(f"summary_csv_path: {summary_csv_path}")
    if comparison_paths:
        print(f"comparison_markdown_path: {comparison_paths['markdown']}")
    for command, replay_paths in sample_replay_paths.items():
        for replay_path in replay_paths:
            print(f"sample_replay_path[{command}]: {replay_path}")
    print()
    _print_table(rows)
    return 0 if all(result.success for result in parse_results) else 1


def _build_scenario_spec(args: argparse.Namespace) -> ScenarioSpec:
    raw = yaml.safe_load(args.scenario.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "simulation_config_path" in raw:
        env_config = load_environment_config(args.scenario)
        simulation_config = load_simulation_config(env_config.simulation_config_path)
        return ScenarioSpec(
            scenario_id=simulation_config.scenario_id,
            simulation_config_path=env_config.simulation_config_path,
            env_config_path=str(args.scenario),
            controlled_agent_id=args.controlled_agent or env_config.controlled_agent_id,
            teammate_policy_id=env_config.teammate_policy_id,
            opponent_policy_ids=[args.opponent_policy, args.opponent_policy],
            description="Command profile comparison suite",
        )
    simulation_config = load_simulation_config(args.scenario)
    return ScenarioSpec(
        scenario_id=simulation_config.scenario_id,
        simulation_config_path=str(args.scenario),
        env_config_path=None,
        controlled_agent_id=(
            args.controlled_agent or _default_controlled_agent_id(simulation_config)
        ),
        teammate_policy_id=args.base_policy,
        opponent_policy_ids=[args.opponent_policy, args.opponent_policy],
        description="Command profile comparison suite",
    )


def _default_controlled_agent_id(config) -> str:
    for team in config.teams:
        if team.team_id != 0:
            continue
        for agent in team.agents:
            if agent.role == "ranged_dps":
                return agent.agent_id
        if team.agents:
            return team.agents[0].agent_id
    msg = "could not infer a team 0 controlled agent"
    raise ValueError(msg)


def _write_profile(path: Path, profile: BehaviorProfile) -> None:
    path.write_text(
        yaml.safe_dump(profile.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def _row_from_result(
    command: str,
    profile: BehaviorProfile,
    aggregate_metrics: dict[str, float],
) -> dict[str, object]:
    return {
        "command": command,
        "profile_id": profile.profile_id,
        "success": True,
        "attack_action_rate": aggregate_metrics.get("mean_attack_action_rate", 0.0),
        "retreat_action_rate": aggregate_metrics.get("mean_retreat_action_rate", 0.0),
        "avg_distance_to_ally": aggregate_metrics.get("mean_avg_distance_to_ally", 0.0),
        "avg_distance_to_nearest_enemy": aggregate_metrics.get(
            "mean_avg_distance_to_nearest_enemy", 0.0
        ),
        "win_rate": aggregate_metrics.get("win_rate", 0.0),
    }


def _failed_row(command: str, parse_result: BehaviorProfileParseResult) -> dict[str, object]:
    return {
        "command": command,
        "profile_id": "",
        "success": False,
        "attack_action_rate": 0.0,
        "retreat_action_rate": 0.0,
        "avg_distance_to_ally": 0.0,
        "avg_distance_to_nearest_enemy": 0.0,
        "win_rate": 0.0,
        "errors": "; ".join(parse_result.errors),
        "unsupported_requests": "; ".join(parse_result.unsupported_requests),
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(SUMMARY_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in SUMMARY_FIELDS})


def _print_table(rows: list[dict[str, object]]) -> None:
    widths = {field: max(len(field), 12) for field in SUMMARY_FIELDS}
    for row in rows:
        for field in SUMMARY_FIELDS:
            widths[field] = max(widths[field], len(_format_value(row.get(field, ""))))
    print("  ".join(field.ljust(widths[field]) for field in SUMMARY_FIELDS))
    print("  ".join("-" * widths[field] for field in SUMMARY_FIELDS))
    for row in rows:
        print(
            "  ".join(
                _format_value(row.get(field, "")).ljust(widths[field]) for field in SUMMARY_FIELDS
            )
        )


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
