"""Compare manual behavior profiles across fixed seeds."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from combatrl.agents.base import AgentPolicy
from combatrl.agents.profiled_bot import ProfiledBot
from combatrl.agents.registry import create_policy
from combatrl.evaluation.benchmark_suite import BenchmarkSuite
from combatrl.evaluation.reports import write_comparison_report
from combatrl.profiles.loader import load_profile_by_id
from combatrl.profiles.metrics import (
    METRIC_FIELDS,
    ProfileMetricsAccumulator,
    profile_behavior_separation_score,
)
from combatrl.profiles.metrics import (
    aggregate_metric_dicts as aggregate_profile_metric_dicts,
)
from combatrl.replay.validators import validate_replay
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.actions import ActionCommand
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.evaluation import PolicySpec, ScenarioSpec
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import make_event_log
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.snapshots import build_replay_frame, build_replay_summary

DEFAULT_SCENARIO = Path("configs/env/mvp_2v2_elimination.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare CombatRL behavior profiles.")
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument(
        "--profiles",
        nargs="+",
        default=["aggressive", "defensive", "protective", "kiter", "balanced"],
    )
    parser.add_argument("--base-policy", default="aggressive")
    parser.add_argument("--opponent-policy", default="aggressive")
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--num-seeds", type=int, default=30)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument(
        "--replay-dir",
        type=Path,
        default=Path("artifacts/replays/profile_comparisons"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/metrics/profile_comparisons"),
    )
    parser.add_argument("--controlled-agent", default=None)
    parser.add_argument("--max-ticks", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    seeds = (
        args.seeds if args.seeds else list(range(args.seed_start, args.seed_start + args.num_seeds))
    )
    run_id = datetime.now(UTC).strftime("run_%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    replay_root = args.replay_dir / run_id
    if args.save_replays:
        replay_root.mkdir(parents=True, exist_ok=True)
    if args.max_ticks is not None:
        return _run_legacy_profile_comparison(
            args=args,
            seeds=seeds,
            output_dir=output_dir,
            replay_root=replay_root,
        )

    config = load_simulation_config(args.scenario)
    controlled_agent_id = args.controlled_agent or _default_controlled_agent_id(config)
    scenario_spec = ScenarioSpec(
        scenario_id=config.scenario_id,
        simulation_config_path=str(args.scenario),
        env_config_path=None,
        controlled_agent_id=controlled_agent_id,
        teammate_policy_id=args.base_policy,
        opponent_policy_ids=[args.opponent_policy, args.opponent_policy],
        description="Profile comparison suite",
    )
    suite = BenchmarkSuite(output_dir=output_dir / "evaluations")
    results = []
    profile_rows: list[dict[str, object]] = []
    sample_replay_paths: dict[str, str] = {}
    for profile_id in args.profiles:
        result = suite.run(
            scenario_spec=scenario_spec,
            policy_spec=PolicySpec(
                policy_id=f"profiled:{args.base_policy}:{profile_id}",
                policy_type="profiled",
                base_policy_id=args.base_policy,
                profile_id=profile_id,
                controlled_agent_id=controlled_agent_id,
            ),
            seeds=seeds,
            save_replays=args.save_replays,
            replay_sample_count=1,
        )
        results.append(result)
        row = _row_from_result(profile_id, len(seeds), result.aggregate_metrics)
        profile_rows.append(row)
        if result.replay_sample_paths:
            replay_path = result.replay_sample_paths[0]
            validate_replay(replay_path)
            sample_replay_paths[profile_id] = replay_path

    baseline_row = _select_baseline_row(profile_rows)
    for row in profile_rows:
        row["profile_behavior_separation_score"] = profile_behavior_separation_score(
            {field: float(row[field]) for field in METRIC_FIELDS},
            {field: float(baseline_row[field]) for field in METRIC_FIELDS},
        )
    comparison_paths = write_comparison_report(results, output_dir / "comparison_report")

    json_path = output_dir / "profile_comparison_summary.json"
    csv_path = output_dir / "profile_comparison_summary.csv"
    payload = {
        "metrics_schema_version": "1.0",
        "scenario": str(args.scenario),
        "profiles": args.profiles,
        "base_policy": args.base_policy,
        "opponent_policy": args.opponent_policy,
        "seeds": seeds,
        "controlled_agent": args.controlled_agent,
        "rows": profile_rows,
        "sample_replay_paths": sample_replay_paths,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_csv(csv_path, profile_rows)

    print(f"json_metrics_path: {json_path}")
    print(f"csv_metrics_path: {csv_path}")
    print(f"comparison_markdown_path: {comparison_paths['markdown']}")
    for profile_id, replay_path in sample_replay_paths.items():
        print(f"sample_replay_path[{profile_id}]: {replay_path}")
    print()
    print_comparison_table(profile_rows)
    return 0


def _run_legacy_profile_comparison(
    *,
    args: argparse.Namespace,
    seeds: list[int],
    output_dir: Path,
    replay_root: Path,
) -> int:
    """Preserve the P8 max-ticks comparison path for quick local overrides."""
    profile_rows: list[dict[str, object]] = []
    sample_replay_paths: dict[str, str] = {}
    for profile_id in args.profiles:
        episode_metrics: list[dict[str, float]] = []
        profile_replay_path: Path | None = None
        for seed_index, seed in enumerate(seeds):
            replay_path = (
                replay_root / profile_id if args.save_replays and seed_index == 0 else None
            )
            metrics, replay_path = run_profile_episode(
                scenario_path=args.scenario,
                profile_id=profile_id,
                base_policy_id=args.base_policy,
                opponent_policy_id=args.opponent_policy,
                seed=seed,
                controlled_agent_id=args.controlled_agent,
                replay_output_root=replay_path,
                max_ticks=args.max_ticks,
            )
            episode_metrics.append(metrics)
            if replay_path is not None:
                validate_replay(replay_path)
                profile_replay_path = replay_path

        aggregate = aggregate_profile_metric_dicts(episode_metrics)
        row: dict[str, object] = {"profile_id": profile_id, "seed_count": len(seeds)}
        row.update(aggregate)
        profile_rows.append(row)
        if profile_replay_path is not None:
            sample_replay_paths[profile_id] = str(profile_replay_path)

    baseline_row = _select_baseline_row(profile_rows)
    for row in profile_rows:
        row["profile_behavior_separation_score"] = profile_behavior_separation_score(
            {field: float(row[field]) for field in METRIC_FIELDS},
            {field: float(baseline_row[field]) for field in METRIC_FIELDS},
        )

    json_path = output_dir / "profile_comparison_summary.json"
    csv_path = output_dir / "profile_comparison_summary.csv"
    payload = {
        "metrics_schema_version": "1.0",
        "scenario": str(args.scenario),
        "profiles": args.profiles,
        "base_policy": args.base_policy,
        "opponent_policy": args.opponent_policy,
        "seeds": seeds,
        "controlled_agent": args.controlled_agent,
        "rows": profile_rows,
        "sample_replay_paths": sample_replay_paths,
        "mode": "legacy_max_ticks",
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_csv(csv_path, profile_rows)

    print(f"json_metrics_path: {json_path}")
    print(f"csv_metrics_path: {csv_path}")
    for profile_id, replay_path in sample_replay_paths.items():
        print(f"sample_replay_path[{profile_id}]: {replay_path}")
    print()
    print_comparison_table(profile_rows)
    return 0


def _row_from_result(
    profile_id: str,
    seed_count: int,
    aggregate_metrics: dict[str, float],
) -> dict[str, object]:
    return {
        "profile_id": profile_id,
        "seed_count": seed_count,
        "avg_damage_dealt": aggregate_metrics.get("mean_damage_dealt", 0.0),
        "avg_damage_taken": aggregate_metrics.get("mean_damage_taken", 0.0),
        "avg_survival_ticks": aggregate_metrics.get("mean_survival_ticks", 0.0),
        "avg_distance_to_nearest_enemy": aggregate_metrics.get(
            "mean_avg_distance_to_nearest_enemy", 0.0
        ),
        "avg_distance_to_ally": aggregate_metrics.get("mean_avg_distance_to_ally", 0.0),
        "attack_action_rate": aggregate_metrics.get("mean_attack_action_rate", 0.0),
        "retreat_action_rate": aggregate_metrics.get("mean_retreat_action_rate", 0.0),
        "low_hp_chase_rate": aggregate_metrics.get("mean_low_hp_chase_rate", 0.0),
        "shared_target_rate": aggregate_metrics.get("mean_shared_target_rate", 0.0),
        "ally_peel_rate": aggregate_metrics.get("mean_ally_peel_rate", 0.0),
        "profile_behavior_separation_score": 0.0,
        "win_rate": aggregate_metrics.get("win_rate", 0.0),
    }


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


def run_profile_episode(
    *,
    scenario_path: Path,
    profile_id: str,
    base_policy_id: str,
    opponent_policy_id: str,
    seed: int,
    controlled_agent_id: str | None,
    replay_output_root: Path | None,
    max_ticks: int | None,
) -> tuple[dict[str, float], Path | None]:
    config = load_simulation_config(scenario_path)
    if max_ticks is not None:
        config = config.model_copy(update={"max_ticks": max_ticks})
    engine = SimulationEngine(config=config, seed=seed)
    policies = build_profile_comparison_policies(
        state=engine.state,
        profile_id=profile_id,
        base_policy_id=base_policy_id,
        opponent_policy_id=opponent_policy_id,
        seed=seed,
        controlled_agent_id=controlled_agent_id,
    )
    accumulator = ProfileMetricsAccumulator(team_id=0, focus_agent_id=controlled_agent_id)
    accumulator.observe_state(engine.state)

    writer: ReplayWriter | None = None
    replay_path: Path | None = None
    if replay_output_root is not None:
        writer = ReplayWriter(output_root=replay_output_root, use_timestamp=False)
        replay_path = writer.start_match(config=config, state=engine.state, seed=seed)
        initial_events = [
            make_event_log(
                match_id=engine.state.match_id,
                tick=0,
                index=0,
                event_type="match_started",
                payload={
                    "scenario_id": config.scenario_id,
                    "seed": seed,
                    "profile_id": profile_id,
                    "base_policy": base_policy_id,
                    "opponent_policy": opponent_policy_id,
                    "controlled_agent_id": controlled_agent_id,
                },
            )
        ]
        writer.write_events(initial_events)
        writer.write_frame(build_replay_frame(engine.state, initial_events))

    try:
        while not engine.state.terminal:
            actions, metadata = policy_actions(engine.state, policies)
            accumulator.observe_actions(engine.state, actions)
            engine.step(actions, action_metadata=metadata)
            accumulator.observe_events(engine.state, engine.last_events)
            accumulator.observe_state(engine.state)
            if writer is not None:
                writer.write_events(engine.last_events)
                writer.write_frame(build_replay_frame(engine.state, engine.last_events))
    finally:
        if writer is not None:
            summary = build_replay_summary(
                config=config,
                state=engine.state,
                frame_count=writer.frame_count,
                event_count=writer.event_count,
            )
            replay_path = writer.finish(summary)

    return accumulator.finalize(engine.state), replay_path


def build_profile_comparison_policies(
    *,
    state: MatchState,
    profile_id: str,
    base_policy_id: str,
    opponent_policy_id: str,
    seed: int,
    controlled_agent_id: str | None,
) -> dict[str, AgentPolicy]:
    profile = load_profile_by_id(profile_id)
    policies: dict[str, AgentPolicy] = {}
    for index, agent_id in enumerate(sorted(state.agents)):
        agent = state.agents[agent_id]
        if agent.team_id == 0:
            base_policy = create_policy(base_policy_id, seed=seed + index)
            should_profile = controlled_agent_id is None or controlled_agent_id == agent_id
            policies[agent_id] = (
                ProfiledBot(base_policy, profile) if should_profile else base_policy
            )
        else:
            policies[agent_id] = create_policy(opponent_policy_id, seed=seed + 100 + index)
        policies[agent_id].reset(seed + index)
    return policies


def policy_actions(
    state: MatchState,
    policies: dict[str, AgentPolicy],
) -> tuple[list[ActionCommand], dict[str, dict[str, object]]]:
    actions: list[ActionCommand] = []
    metadata: dict[str, dict[str, object]] = {}
    for agent_id in sorted(state.agents):
        policy = policies[agent_id]
        action = policy.select_action(state, agent_id)
        actions.append(action)
        metadata[agent_id] = {
            "policy_id": policy.policy_id,
            "profile_id": getattr(policy, "profile_id", None),
            "valid": True,
            "fallback_used": False,
        }
    return actions, metadata


def print_comparison_table(rows: list[dict[str, object]]) -> None:
    columns = (
        "profile_id",
        "avg_damage_dealt",
        "avg_survival_ticks",
        "avg_distance_to_ally",
        "avg_distance_to_nearest_enemy",
        "attack_action_rate",
        "retreat_action_rate",
        "win_rate",
    )
    widths = {column: max(len(column), 10) for column in columns}
    for row in rows:
        for column in columns:
            widths[column] = max(widths[column], len(_format_value(row[column])))
    print("  ".join(column.ljust(widths[column]) for column in columns))
    print("  ".join("-" * widths[column] for column in columns))
    for row in rows:
        print("  ".join(_format_value(row[column]).ljust(widths[column]) for column in columns))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = ["profile_id", "seed_count", *METRIC_FIELDS]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _select_baseline_row(rows: list[dict[str, object]]) -> dict[str, object]:
    for row in rows:
        if row["profile_id"] == "balanced":
            return row
    return rows[0]


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
