"""Evaluate one CombatRL policy/profile/checkpoint across fixed seeds."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from combatrl.evaluation.benchmark_suite import BenchmarkSuite
from combatrl.schemas.configs import load_environment_config, load_simulation_config
from combatrl.schemas.evaluation import PolicySpec, ScenarioSpec

DEFAULT_SCENARIO = Path("configs/env/gym_2v2_controlled_ranged.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a CombatRL policy across fixed seeds.")
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--env-config", type=Path, default=None)
    parser.add_argument("--simulation-config", type=Path, default=None)
    parser.add_argument(
        "--policy-type",
        choices=["heuristic", "ppo_checkpoint", "random", "profiled"],
        required=True,
    )
    parser.add_argument("--policy-id", default=None)
    parser.add_argument("--base-policy", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--controlled-agent", default=None)
    parser.add_argument("--teammate-policy", default=None)
    parser.add_argument("--opponents", nargs="+", default=None)
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--num-seeds", type=int, default=30)
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument("--replay-sample-count", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/metrics/evaluations"))
    ppo_mode = parser.add_mutually_exclusive_group()
    ppo_mode.add_argument("--deterministic", action="store_true", default=True)
    ppo_mode.add_argument("--stochastic", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        scenario_spec = build_scenario_spec(args)
        policy_spec = build_policy_spec(args)
        seeds = parse_seeds(args)
        result = BenchmarkSuite(args.output_dir).run(
            scenario_spec=scenario_spec,
            policy_spec=policy_spec,
            seeds=seeds,
            save_replays=args.save_replays,
            replay_sample_count=args.replay_sample_count,
        )
    except Exception as exc:
        print(f"evaluate_policy failed: {exc}", file=sys.stderr)
        return 1

    run_dir = Path(result.per_match_metrics_path).parent
    aggregate_json_path = run_dir / "evaluation_result.json"
    markdown_report_path = run_dir / "evaluation_report.md"
    print_summary(result.aggregate_metrics)
    print(f"aggregate_json_path: {aggregate_json_path}")
    print(f"per_match_csv_path: {result.per_match_metrics_path}")
    print(f"markdown_report_path: {markdown_report_path}")
    for replay_path in result.replay_sample_paths:
        print(f"sample_replay_path: {replay_path}")
    return 0


def build_scenario_spec(args: argparse.Namespace) -> ScenarioSpec:
    env_config_path = args.env_config or _env_config_path_from_scenario_arg(args.scenario)
    if env_config_path is not None:
        env_config = load_environment_config(env_config_path)
        simulation_config_path = args.simulation_config or Path(env_config.simulation_config_path)
        simulation_config = load_simulation_config(simulation_config_path)
        return ScenarioSpec(
            scenario_id=simulation_config.scenario_id,
            simulation_config_path=str(simulation_config_path),
            env_config_path=str(env_config_path),
            controlled_agent_id=args.controlled_agent or env_config.controlled_agent_id,
            teammate_policy_id=args.teammate_policy or env_config.teammate_policy_id,
            opponent_policy_ids=args.opponents or env_config.opponent_policy_ids,
            description=f"Loaded from {env_config_path}",
        )

    simulation_config_path = args.simulation_config or args.scenario
    simulation_config = load_simulation_config(simulation_config_path)
    controlled_agent_id = args.controlled_agent or _first_team0_agent_id(
        simulation_config.model_dump()
    )
    return ScenarioSpec(
        scenario_id=simulation_config.scenario_id,
        simulation_config_path=str(simulation_config_path),
        env_config_path=None,
        controlled_agent_id=controlled_agent_id,
        teammate_policy_id=args.teammate_policy,
        opponent_policy_ids=args.opponents or ["aggressive", "random"],
        description=f"Loaded from {simulation_config_path}",
    )


def build_policy_spec(args: argparse.Namespace) -> PolicySpec:
    profile_id = args.profile
    policy_id = args.policy_id
    if args.policy_type == "random":
        policy_id = policy_id or "random"
    elif args.policy_type == "profiled":
        if profile_id is None:
            msg = "--profile is required for --policy-type profiled"
            raise ValueError(msg)
        policy_id = policy_id or f"profiled:{args.base_policy or 'aggressive'}:{profile_id}"
    elif args.policy_type == "ppo_checkpoint":
        if args.checkpoint is None:
            msg = "--checkpoint is required for --policy-type ppo_checkpoint"
            raise ValueError(msg)
        policy_id = policy_id or Path(args.checkpoint).stem
    else:
        policy_id = policy_id or args.base_policy or "aggressive"

    return PolicySpec(
        policy_id=policy_id,
        policy_type=args.policy_type,
        checkpoint_path=None if args.checkpoint is None else str(args.checkpoint),
        base_policy_id=args.base_policy,
        profile_id=profile_id,
        controlled_agent_id=args.controlled_agent,
        notes="stochastic" if args.stochastic else None,
    )


def parse_seeds(args: argparse.Namespace) -> list[int]:
    if args.seeds:
        return [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
    if args.num_seeds <= 0:
        msg = "--num-seeds must be positive"
        raise ValueError(msg)
    return list(range(args.seed_start, args.seed_start + args.num_seeds))


def print_summary(metrics: dict[str, float]) -> None:
    columns = ["num_matches", "win_rate", "loss_rate", "timeout_rate", "mean_damage_dealt"]
    widths = {column: max(len(column), 12) for column in columns}
    values = {column: _format(metrics.get(column, 0.0)) for column in columns}
    print("  ".join(column.ljust(widths[column]) for column in columns))
    print("  ".join("-" * widths[column] for column in columns))
    print("  ".join(values[column].ljust(widths[column]) for column in columns))


def _env_config_path_from_scenario_arg(path: Path) -> Path | None:
    raw = _read_yaml(path)
    if isinstance(raw, dict) and "simulation_config_path" in raw and "controlled_agent_id" in raw:
        return path
    return None


def _read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _first_team0_agent_id(config: dict[str, Any]) -> str:
    for team in config.get("teams", []):
        if team.get("team_id") != 0:
            continue
        agents = team.get("agents", [])
        if agents:
            return str(agents[0]["agent_id"])
    msg = "could not infer controlled agent; pass --controlled-agent"
    raise ValueError(msg)


def _format(value: float | int | str | None) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
