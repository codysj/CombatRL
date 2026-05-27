"""Fixed-seed benchmark runner for CombatRL policies and profiles."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np

from combatrl.agents.base import AgentPolicy
from combatrl.agents.profiled_bot import ProfiledBot
from combatrl.agents.registry import create_policy
from combatrl.core.constants import (
    ACTION_SCHEMA_VERSION,
    METRICS_SCHEMA_VERSION,
    OBSERVATION_SCHEMA_VERSION,
)
from combatrl.envs import CombatRLGymEnv
from combatrl.evaluation.aggregate import aggregate_match_records
from combatrl.evaluation.metrics import compute_match_metrics_from_frames_events
from combatrl.evaluation.reports import (
    write_evaluation_json,
    write_markdown_report,
    write_per_match_csv,
    write_per_match_jsonl,
)
from combatrl.profiles.loader import load_profile_by_id
from combatrl.replay.validators import validate_replay
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.actions import ActionCommand
from combatrl.schemas.configs import EnvironmentConfig, load_simulation_config
from combatrl.schemas.evaluation import (
    EvaluationResult,
    MatchEvaluationRecord,
    PolicySpec,
    ScenarioSpec,
)
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import EventLog, ReplayFrame, make_event_log
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.snapshots import build_replay_frame, build_replay_summary


class PredictPolicy(Protocol):
    """Minimal Stable-Baselines3 prediction interface."""

    def predict(self, observation: np.ndarray, deterministic: bool = True) -> tuple[object, object]:
        """Return a predicted action and optional recurrent state."""


class BenchmarkSuite:
    """Run seeded scenarios and persist local evaluation artifacts."""

    def __init__(self, output_dir: str | Path = "artifacts/metrics/evaluations") -> None:
        self.output_dir = Path(output_dir)

    def run(
        self,
        scenario_spec: ScenarioSpec,
        policy_spec: PolicySpec,
        seeds: list[int],
        save_replays: bool = False,
        replay_sample_count: int = 3,
    ) -> EvaluationResult:
        """Run one deterministic match for each seed and save reports."""
        if not seeds:
            msg = "seeds must contain at least one seed"
            raise ValueError(msg)
        sorted_seeds = sorted(int(seed) for seed in seeds)
        evaluation_id = _evaluation_id(scenario_spec, policy_spec, sorted_seeds)
        run_dir = self.output_dir / evaluation_id
        run_dir.mkdir(parents=True, exist_ok=True)
        replay_root = run_dir / "replays"
        sample_seed_set = set(sorted_seeds[: max(0, replay_sample_count)])

        records: list[MatchEvaluationRecord] = []
        replay_sample_paths: list[str] = []
        for seed in sorted_seeds:
            should_save_replay = save_replays or seed in sample_seed_set
            record, replay_path = self._run_one_match(
                scenario_spec=scenario_spec,
                policy_spec=policy_spec,
                seed=seed,
                replay_root=replay_root if should_save_replay else None,
            )
            records.append(record.model_copy(update={"evaluation_id": evaluation_id}))
            if replay_path is not None and seed in sample_seed_set:
                replay_sample_paths.append(str(replay_path))

        csv_path = write_per_match_csv(records, run_dir / "per_match_metrics.csv")
        jsonl_path = write_per_match_jsonl(records, run_dir / "per_match_metrics.jsonl")
        aggregate_metrics = aggregate_match_records(records)
        result = EvaluationResult(
            metrics_schema_version=METRICS_SCHEMA_VERSION,
            evaluation_id=evaluation_id,
            scenario_id=scenario_spec.scenario_id,
            policy_id=policy_spec.policy_id,
            opponent_id=_opponent_id(scenario_spec.opponent_policy_ids),
            profile_id=policy_spec.profile_id,
            num_matches=len(records),
            seed_start=min(sorted_seeds),
            aggregate_metrics=aggregate_metrics,
            per_match_metrics_path=str(csv_path),
            replay_sample_paths=replay_sample_paths,
        )
        write_evaluation_json(result, run_dir / "evaluation_result.json")
        write_markdown_report(result, records, run_dir / "evaluation_report.md")
        _ = jsonl_path
        return result

    def _run_one_match(
        self,
        *,
        scenario_spec: ScenarioSpec,
        policy_spec: PolicySpec,
        seed: int,
        replay_root: Path | None,
    ) -> tuple[MatchEvaluationRecord, Path | None]:
        if policy_spec.policy_type == "ppo_checkpoint":
            return self._run_one_gym_match(
                scenario_spec=scenario_spec,
                policy_spec=policy_spec,
                seed=seed,
                replay_root=replay_root,
            )
        return self._run_one_scripted_match(
            scenario_spec=scenario_spec,
            policy_spec=policy_spec,
            seed=seed,
            replay_root=replay_root,
        )

    def _run_one_scripted_match(
        self,
        *,
        scenario_spec: ScenarioSpec,
        policy_spec: PolicySpec,
        seed: int,
        replay_root: Path | None,
    ) -> tuple[MatchEvaluationRecord, Path | None]:
        config = load_simulation_config(scenario_spec.simulation_config_path)
        engine = SimulationEngine(config=config, seed=seed)
        policies = _build_scripted_policies(engine.state, scenario_spec, policy_spec, seed)
        frames: list[ReplayFrame] = []
        events: list[EventLog] = []
        writer, replay_path = _start_replay_writer(
            replay_root=replay_root,
            config=config,
            state=engine.state,
            seed=seed,
            controlled_agent_id=scenario_spec.controlled_agent_id,
            policy_id=policy_spec.policy_id,
        )
        initial_events = [
            make_event_log(
                match_id=engine.state.match_id,
                tick=0,
                index=0,
                event_type="match_started",
                payload={
                    "scenario_id": config.scenario_id,
                    "seed": seed,
                    "controlled_agent_id": scenario_spec.controlled_agent_id,
                    "policy_id": policy_spec.policy_id,
                    "profile_id": policy_spec.profile_id,
                },
            )
        ]
        frames.append(build_replay_frame(engine.state, initial_events))
        events.extend(initial_events)
        if writer is not None:
            writer.write_events(initial_events)
            writer.write_frame(frames[-1])

        try:
            while not engine.state.terminal:
                actions, metadata = _policy_actions(engine.state, policies)
                engine.step(actions, action_metadata=metadata)
                step_events = engine.last_events
                frame = build_replay_frame(engine.state, step_events)
                events.extend(step_events)
                frames.append(frame)
                if writer is not None:
                    writer.write_events(step_events)
                    writer.write_frame(frame)
        finally:
            if writer is not None:
                replay_path = writer.finish(
                    build_replay_summary(
                        config=config,
                        state=engine.state,
                        frame_count=writer.frame_count,
                        event_count=writer.event_count,
                    )
                )
                validate_replay(replay_path)

        metrics = compute_match_metrics_from_frames_events(
            frames,
            events,
            scenario_spec.controlled_agent_id,
        )
        return _record_from_metrics(
            scenario_spec=scenario_spec,
            policy_spec=policy_spec,
            seed=seed,
            match_id=engine.state.match_id,
            replay_path=replay_path,
            metrics=metrics,
        ), replay_path

    def _run_one_gym_match(
        self,
        *,
        scenario_spec: ScenarioSpec,
        policy_spec: PolicySpec,
        seed: int,
        replay_root: Path | None,
    ) -> tuple[MatchEvaluationRecord, Path | None]:
        env_config = _env_config_for_scenario(scenario_spec)
        env = CombatRLGymEnv(env_config, render_mode=None)
        model = _load_ppo(policy_spec)
        rng = np.random.default_rng(seed)
        frames: list[ReplayFrame] = []
        events: list[EventLog] = []
        writer: ReplayWriter | None = None
        replay_path: Path | None = None
        try:
            observation, _ = env.reset(seed=seed)
            engine = _require_engine(env)
            writer, replay_path = _start_replay_writer(
                replay_root=replay_root,
                config=env.simulation_config,
                state=engine.state,
                seed=seed,
                controlled_agent_id=scenario_spec.controlled_agent_id,
                policy_id=policy_spec.policy_id,
            )
            initial_events = [
                make_event_log(
                    match_id=engine.state.match_id,
                    tick=0,
                    index=0,
                    event_type="match_started",
                    payload={
                        "scenario_id": env.simulation_config.scenario_id,
                        "seed": seed,
                        "controlled_agent_id": scenario_spec.controlled_agent_id,
                        "policy_id": policy_spec.policy_id,
                        "checkpoint_path": policy_spec.checkpoint_path,
                    },
                )
            ]
            frames.append(build_replay_frame(engine.state, initial_events))
            events.extend(initial_events)
            if writer is not None:
                writer.write_events(initial_events)
                writer.write_frame(frames[-1])

            terminated = False
            truncated = False
            while not (terminated or truncated):
                if policy_spec.policy_type == "ppo_checkpoint":
                    action, _ = model.predict(
                        observation,
                        deterministic=_ppo_deterministic(policy_spec),
                    )
                    action_id = int(np.asarray(action).item())
                else:
                    mask = env.action_codec.valid_action_mask(
                        engine.state, env.env_config.controlled_agent_id
                    )
                    action_id = int(rng.choice(np.flatnonzero(mask)))
                observation, _, terminated, truncated, _ = env.step(action_id)
                engine = _require_engine(env)
                step_events = engine.last_events
                frame = build_replay_frame(engine.state, step_events)
                events.extend(step_events)
                frames.append(frame)
                if writer is not None:
                    writer.write_events(step_events)
                    writer.write_frame(frame)

            engine = _require_engine(env)
            if writer is not None:
                replay_path = writer.finish(
                    build_replay_summary(
                        config=env.simulation_config,
                        state=engine.state,
                        frame_count=writer.frame_count,
                        event_count=writer.event_count,
                    )
                )
                validate_replay(replay_path)
            metrics = compute_match_metrics_from_frames_events(
                frames,
                events,
                scenario_spec.controlled_agent_id,
            )
            return _record_from_metrics(
                scenario_spec=scenario_spec,
                policy_spec=policy_spec,
                seed=seed,
                match_id=engine.state.match_id,
                replay_path=replay_path,
                metrics=metrics,
            ), replay_path
        finally:
            if writer is not None:
                writer.close()
            env.close()


def _build_scripted_policies(
    state: MatchState,
    scenario_spec: ScenarioSpec,
    policy_spec: PolicySpec,
    seed: int,
) -> dict[str, AgentPolicy]:
    controlled_team_id = state.agents[scenario_spec.controlled_agent_id].team_id
    policies: dict[str, AgentPolicy] = {}
    opponent_index = 0
    teammate_index = 0
    for index, agent_id in enumerate(sorted(state.agents)):
        agent = state.agents[agent_id]
        if agent_id == scenario_spec.controlled_agent_id:
            policy = _controlled_scripted_policy(policy_spec, seed + index)
        elif agent.team_id == controlled_team_id:
            policy = create_policy(
                scenario_spec.teammate_policy_id or "random", seed=seed + 100 + teammate_index
            )
            teammate_index += 1
        else:
            policy_id = _policy_for_index(scenario_spec.opponent_policy_ids, opponent_index)
            policy = create_policy(policy_id, seed=seed + 200 + opponent_index)
            opponent_index += 1
        policy.reset(seed + index)
        policies[agent_id] = policy
    return policies


def _controlled_scripted_policy(policy_spec: PolicySpec, seed: int) -> AgentPolicy:
    if policy_spec.policy_type == "random":
        return create_policy("random", seed=seed)
    if policy_spec.policy_type == "profiled":
        base_policy_id = policy_spec.base_policy_id or "aggressive"
        profile_id = policy_spec.profile_id
        if profile_id is None:
            msg = "profiled policies require profile_id"
            raise ValueError(msg)
        return ProfiledBot(create_policy(base_policy_id, seed=seed), load_profile_by_id(profile_id))
    return create_policy(policy_spec.policy_id, seed=seed)


def _policy_actions(
    state: MatchState,
    policies: dict[str, AgentPolicy],
) -> tuple[list[ActionCommand], dict[str, dict[str, object]]]:
    actions: list[ActionCommand] = []
    metadata: dict[str, dict[str, object]] = {}
    for agent_id in sorted(state.agents):
        policy = policies[agent_id]
        actions.append(policy.select_action(state, agent_id))
        metadata[agent_id] = {
            "policy_id": policy.policy_id,
            "profile_id": getattr(policy, "profile_id", None),
            "valid": True,
            "fallback_used": False,
        }
    return actions, metadata


def _env_config_for_scenario(scenario_spec: ScenarioSpec) -> EnvironmentConfig:
    return EnvironmentConfig(
        env_id=f"CombatRL-Eval-{scenario_spec.scenario_id}",
        simulation_config_path=scenario_spec.simulation_config_path,
        controlled_agent_id=scenario_spec.controlled_agent_id,
        opponent_policy_ids=scenario_spec.opponent_policy_ids,
        teammate_policy_id=scenario_spec.teammate_policy_id,
        observation_schema_version=OBSERVATION_SCHEMA_VERSION,
        action_schema_version=ACTION_SCHEMA_VERSION,
        capture_replays=False,
        replay_sample_rate=0.0,
        decision_interval_ticks=4,
        terminate_on_controlled_death=False,
    )


def _load_ppo(policy_spec: PolicySpec) -> PredictPolicy:
    if policy_spec.policy_type != "ppo_checkpoint":
        msg = "only ppo_checkpoint policies can load PPO models"
        raise ValueError(msg)
    if policy_spec.checkpoint_path is None:
        msg = "ppo_checkpoint policies require checkpoint_path"
        raise ValueError(msg)
    from stable_baselines3 import PPO

    return cast(PredictPolicy, PPO.load(policy_spec.checkpoint_path))


def _ppo_deterministic(policy_spec: PolicySpec) -> bool:
    return policy_spec.notes != "stochastic"


def _record_from_metrics(
    *,
    scenario_spec: ScenarioSpec,
    policy_spec: PolicySpec,
    seed: int,
    match_id: str,
    replay_path: Path | None,
    metrics: dict[str, Any],
) -> MatchEvaluationRecord:
    return MatchEvaluationRecord(
        evaluation_id="pending",
        match_id=match_id,
        scenario_id=scenario_spec.scenario_id,
        seed=seed,
        policy_id=policy_spec.policy_id,
        opponent_id=_opponent_id(scenario_spec.opponent_policy_ids),
        profile_id=policy_spec.profile_id,
        replay_path=None if replay_path is None else str(replay_path),
        terminal_reason=_optional_str(metrics.get("terminal_reason")),
        winner_team_id=_optional_int(metrics.get("winner_team_id")),
        controlled_team_id=int(metrics.get("controlled_team_id", 0) or 0),
        metrics=metrics,
    )


def _start_replay_writer(
    *,
    replay_root: Path | None,
    config: Any,
    state: MatchState,
    seed: int,
    controlled_agent_id: str,
    policy_id: str,
) -> tuple[ReplayWriter | None, Path | None]:
    if replay_root is None:
        return None, None
    writer = ReplayWriter(
        output_root=replay_root / f"seed_{seed}",
        frame_interval=1,
        use_timestamp=False,
    )
    replay_path = writer.start_match(config=config, state=state, seed=seed)
    _ = controlled_agent_id, policy_id
    return writer, replay_path


def _require_engine(env: CombatRLGymEnv) -> SimulationEngine:
    if env._engine is None:  # noqa: SLF001
        msg = "environment simulator is not initialized"
        raise RuntimeError(msg)
    return env._engine  # noqa: SLF001


def _evaluation_id(scenario_spec: ScenarioSpec, policy_spec: PolicySpec, seeds: list[int]) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return (
        f"eval_{timestamp}_{scenario_spec.scenario_id}_{policy_spec.policy_id}"
        f"_seed-{min(seeds)}-{max(seeds)}"
    ).replace(":", "_")


def _policy_for_index(policy_ids: list[str], index: int) -> str:
    if not policy_ids:
        return "random"
    if index < len(policy_ids):
        return policy_ids[index]
    return policy_ids[-1]


def _opponent_id(opponent_policy_ids: list[str]) -> str:
    return ",".join(opponent_policy_ids) if opponent_policy_ids else "random"


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
