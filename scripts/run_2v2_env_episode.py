"""Run one 2v2 CombatRL Gym episode and optionally save a replay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Protocol

import numpy as np

from combatrl.agents.base import AgentPolicy
from combatrl.agents.registry import create_policy
from combatrl.envs import CombatRLGymEnv
from combatrl.replay.validators import validate_replay
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import make_event_log
from combatrl.sim.snapshots import build_replay_frame, build_replay_summary

DEFAULT_ENV_CONFIG = Path("configs/env/gym_2v2_controlled_ranged.yaml")


class CheckpointPolicy(Protocol):
    """Minimal interface used from Stable-Baselines3 policies."""

    def predict(self, observation: np.ndarray, deterministic: bool = True) -> tuple[object, object]:
        """Return a predicted action and optional state."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one 2v2 episode through CombatRLGymEnv.")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--policy", choices=["random", "scripted", "checkpoint"], default="random")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--save-replay", action="store_true")
    parser.add_argument("--replay-dir", type=Path, default=Path("artifacts/replays"))
    parser.add_argument("--max-env-steps", type=int, default=None)
    parser.add_argument("--scripted-policy-id", default="aggressive")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        summary = run_episode(args)
    except Exception as exc:
        print(f"run_2v2_env_episode failed: {exc}", file=sys.stderr)
        return 1

    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


def run_episode(args: argparse.Namespace) -> dict[str, object]:
    env = CombatRLGymEnv(args.env_config, render_mode=None)
    rng = np.random.default_rng(args.seed)
    replay_writer: ReplayWriter | None = None
    replay_path: Path | None = None
    model: CheckpointPolicy | None = None
    scripted_policy = None
    if args.policy == "checkpoint":
        if args.checkpoint is None:
            msg = "--checkpoint is required when --policy checkpoint is used"
            raise ValueError(msg)
        from stable_baselines3 import PPO

        model = PPO.load(args.checkpoint)
    elif args.policy == "scripted":
        scripted_policy = create_policy(args.scripted_policy_id, seed=args.seed + 500)
        scripted_policy.reset(args.seed + 500)

    try:
        observation, info = env.reset(seed=args.seed)
        engine = _require_engine(env)
        if args.save_replay:
            replay_writer = ReplayWriter(output_root=args.replay_dir, frame_interval=1)
            replay_path = replay_writer.start_match(
                config=env.simulation_config,
                state=engine.state,
                seed=args.seed,
            )
            initial_events = [
                make_event_log(
                    match_id=engine.state.match_id,
                    tick=0,
                    index=0,
                    event_type="match_started",
                    payload={
                        "scenario_id": env.simulation_config.scenario_id,
                        "seed": args.seed,
                        "agent_count": len(engine.state.agents),
                        "controlled_agent_id": env.env_config.controlled_agent_id,
                        "controlled_policy": args.policy,
                    },
                )
            ]
            replay_writer.write_events(initial_events)
            replay_writer.write_frame(build_replay_frame(engine.state, initial_events))

        terminated = False
        truncated = False
        final_reward = 0.0
        env_steps = 0
        final_info = info
        while not (terminated or truncated):
            if args.max_env_steps is not None and env_steps >= args.max_env_steps:
                break
            action = _select_action(
                args=args,
                env=env,
                state=_require_engine(env).state,
                observation=observation,
                rng=rng,
                model=model,
                scripted_policy=scripted_policy,
            )
            observation, reward, terminated, truncated, final_info = env.step(action)
            final_reward += float(reward)
            env_steps += 1
            if replay_writer is not None:
                engine = _require_engine(env)
                step_events = engine.last_events
                replay_writer.write_events(step_events)
                replay_writer.write_frame(build_replay_frame(engine.state, step_events))

        engine = _require_engine(env)
        if replay_writer is not None:
            replay_summary = build_replay_summary(
                config=env.simulation_config,
                state=engine.state,
                frame_count=replay_writer.frame_count,
                event_count=replay_writer.event_count,
            )
            replay_path = replay_writer.finish(replay_summary)
            validate_replay(replay_path)

        return {
            "final_reward": f"{final_reward:.6f}",
            "terminated": str(terminated).lower(),
            "truncated": str(truncated).lower(),
            "terminal_reason": final_info.get("terminal_reason"),
            "winner_team_id": final_info.get("winner_team_id"),
            "final_tick": final_info.get("tick"),
            "controlled_agent_alive": str(final_info.get("controlled_agent_alive")).lower(),
            "ally_alive_count": final_info.get("ally_alive_count"),
            "enemy_alive_count": final_info.get("enemy_alive_count"),
            "env_steps": env_steps,
            "replay_path": replay_path,
        }
    finally:
        if replay_writer is not None:
            replay_writer.close()
        env.close()


def _select_action(
    *,
    args: argparse.Namespace,
    env: CombatRLGymEnv,
    state: MatchState,
    observation: np.ndarray,
    rng: np.random.Generator,
    model: CheckpointPolicy | None,
    scripted_policy: AgentPolicy | None,
) -> int:
    if args.policy == "checkpoint":
        if model is None:
            msg = "checkpoint model was not loaded"
            raise RuntimeError(msg)
        action, _ = model.predict(observation, deterministic=True)
        return int(action)
    if args.policy == "scripted":
        if scripted_policy is None:
            msg = "scripted policy was not created"
            raise RuntimeError(msg)
        command = scripted_policy.select_action(state, env.env_config.controlled_agent_id)
        return env.action_codec.encode(command.action_type)

    mask = env.action_codec.valid_action_mask(state, env.env_config.controlled_agent_id)
    valid_actions = np.flatnonzero(mask)
    return int(rng.choice(valid_actions))


def _require_engine(env: CombatRLGymEnv):
    if env._engine is None:  # noqa: SLF001
        msg = "environment simulator is not initialized"
        raise RuntimeError(msg)
    return env._engine  # noqa: SLF001


if __name__ == "__main__":
    raise SystemExit(main())
