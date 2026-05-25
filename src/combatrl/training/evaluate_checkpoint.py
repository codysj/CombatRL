"""Evaluate saved PPO checkpoints in headless CombatRL environments."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import PPO

from combatrl.envs import CombatRLGymEnv
from combatrl.training.replay_policy import save_policy_replay


def evaluate_checkpoint(
    checkpoint_path: str | Path,
    env_config_path: str | Path,
    num_episodes: int = 20,
    seed_start: int = 1000,
    deterministic: bool = True,
    save_replay: bool = False,
    replay_output_dir: str | Path = "artifacts/replays",
) -> dict[str, Any]:
    """Evaluate one PPO checkpoint and persist a metrics JSON file."""
    if num_episodes <= 0:
        msg = "num_episodes must be positive"
        raise ValueError(msg)

    checkpoint = Path(checkpoint_path)
    model = PPO.load(checkpoint)
    rewards: list[float] = []
    lengths: list[int] = []
    wins = 0
    losses = 0
    timeouts = 0
    invalid_actions = 0
    total_steps = 0
    damage_dealt: list[float] = []
    damage_taken: list[float] = []

    env = CombatRLGymEnv(env_config_path, render_mode=None)
    controlled_team_id = _controlled_team_id(env)
    try:
        for episode_index in range(num_episodes):
            observation, _ = env.reset(seed=seed_start + episode_index)
            terminated = False
            truncated = False
            episode_reward = 0.0
            episode_length = 0
            episode_damage_dealt = 0.0
            episode_damage_taken = 0.0
            final_info: dict[str, Any] = {}
            while not (terminated or truncated):
                action, _ = model.predict(observation, deterministic=deterministic)
                observation, reward, terminated, truncated, info = env.step(int(action))
                episode_reward += float(reward)
                episode_length += 1
                total_steps += 1
                invalid_actions += int(bool(info.get("invalid_action", False)))
                components = info.get("reward_breakdown", {}).get("components", {})
                episode_damage_dealt += max(0.0, float(components.get("damage_dealt", 0.0))) * 100.0
                episode_damage_taken += (
                    max(0.0, -float(components.get("damage_taken_penalty", 0.0))) * 150.0
                )
                final_info = info

            rewards.append(episode_reward)
            lengths.append(episode_length)
            damage_dealt.append(episode_damage_dealt)
            damage_taken.append(episode_damage_taken)
            terminal_reason = final_info.get("terminal_reason")
            winner_team_id = final_info.get("winner_team_id")
            if terminal_reason == "max_ticks":
                timeouts += 1
            elif winner_team_id == controlled_team_id:
                wins += 1
            else:
                losses += 1
    finally:
        env.close()

    metrics: dict[str, Any] = {
        "checkpoint_path": str(checkpoint),
        "env_config_path": str(env_config_path),
        "num_episodes": num_episodes,
        "seed_start": seed_start,
        "deterministic": deterministic,
        "mean_reward": _mean(rewards),
        "std_reward": _std(rewards),
        "win_rate": wins / num_episodes,
        "loss_rate": losses / num_episodes,
        "timeout_rate": timeouts / num_episodes,
        "mean_episode_length": _mean(lengths),
        "invalid_action_rate": invalid_actions / max(total_steps, 1),
        "mean_damage_dealt": _mean(damage_dealt),
        "mean_damage_taken": _mean(damage_taken),
        "created_at_utc": datetime.now(UTC).isoformat(),
    }

    if save_replay:
        replay_path = save_policy_replay(
            model,
            env_config_path,
            replay_output_dir,
            seed=seed_start,
            deterministic=deterministic,
        )
        metrics["sample_replay_path"] = str(replay_path)

    metrics_path = _evaluation_output_path(checkpoint)
    metrics["metrics_path"] = str(metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics


def _evaluation_output_path(checkpoint_path: Path) -> Path:
    run_dir = checkpoint_path.parent
    if run_dir.name == "checkpoints":
        run_dir = run_dir.parent
    return run_dir / "evaluation_metrics.json"


def _controlled_team_id(env: CombatRLGymEnv) -> int:
    controlled_agent_id = env.env_config.controlled_agent_id
    for team in env.simulation_config.teams:
        for agent in team.agents:
            if agent.agent_id == controlled_agent_id:
                return agent.team_id
    msg = f"controlled agent not found in simulation config: {controlled_agent_id}"
    raise ValueError(msg)


def _mean(values: list[float] | list[int]) -> float:
    return float(np.mean(values)) if values else 0.0


def _std(values: list[float] | list[int]) -> float:
    return float(np.std(values)) if values else 0.0
