"""Generate replay artifacts from a trained SB3 policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stable_baselines3 import PPO

from combatrl.envs import CombatRLGymEnv
from combatrl.replay.validators import validate_replay
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.replay import make_event_log
from combatrl.sim.snapshots import build_replay_frame, build_replay_summary


def save_policy_replay(
    model: PPO,
    env_config_path: str | Path,
    output_dir: str | Path,
    *,
    seed: int,
    deterministic: bool = True,
) -> Path:
    """Run one model-controlled episode and write a validated replay."""
    env = CombatRLGymEnv(env_config_path, render_mode=None)
    writer: ReplayWriter | None = None
    try:
        observation, _ = env.reset(seed=seed)
        if env._engine is None:  # noqa: SLF001
            msg = "environment reset did not initialize the simulator"
            raise RuntimeError(msg)

        writer = ReplayWriter(output_root=output_dir, frame_interval=1)
        replay_path = writer.start_match(
            config=env.simulation_config,
            state=env._engine.state,  # noqa: SLF001
            seed=seed,
        )
        initial_events = [
            make_event_log(
                match_id=env._engine.state.match_id,  # noqa: SLF001
                tick=0,
                index=0,
                event_type="match_started",
                payload={
                    "scenario_id": env.simulation_config.scenario_id,
                    "seed": seed,
                    "agent_count": len(env._engine.state.agents),  # noqa: SLF001
                    "policy_id": "ppo",
                },
            )
        ]
        writer.write_events(initial_events)
        writer.write_frame(build_replay_frame(env._engine.state, initial_events))  # noqa: SLF001

        terminated = False
        truncated = False
        while not (terminated or truncated):
            action, _ = model.predict(observation, deterministic=deterministic)
            observation, _, terminated, truncated, _ = env.step(int(action))
            if env._engine is None:  # noqa: SLF001
                msg = "environment simulator became unavailable during replay capture"
                raise RuntimeError(msg)
            step_events = env.last_step_events
            writer.write_events(step_events)
            final_tick_events = env._engine.last_events  # noqa: SLF001
            writer.write_frame(build_replay_frame(env._engine.state, final_tick_events))  # noqa: SLF001

        if env._engine is None:  # noqa: SLF001
            msg = "environment simulator became unavailable before replay finalization"
            raise RuntimeError(msg)
        summary = build_replay_summary(
            config=load_simulation_config(env.env_config.simulation_config_path),
            state=env._engine.state,  # noqa: SLF001
            frame_count=writer.frame_count,
            event_count=writer.event_count,
        )
        replay_path = writer.finish(summary)
        validate_replay(replay_path)
        return replay_path
    finally:
        if writer is not None:
            writer.close()
        env.close()


def replay_summary_dict(replay_path: Path) -> dict[str, Any]:
    """Return the compact replay path payload used by metrics JSON."""
    return {"sample_replay_path": str(replay_path)}
