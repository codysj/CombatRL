"""Run fast headless sanity checks for the CombatRL Gymnasium environment."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

from combatrl.envs import CombatRLGymEnv

DEFAULT_ENV_CONFIG = Path("configs/env/gym_2v2_controlled_ranged.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check CombatRLGymEnv random rollouts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--env-config", type=Path, dest="env_config", default=None)
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_config = args.env_config if args.env_config is not None else args.config
    env = CombatRLGymEnv(env_config)
    rng = np.random.default_rng(args.seed)
    total_reward = 0.0
    terminated_count = 0
    truncated_count = 0
    nan_count = 0
    final_tick = 0

    try:
        observation, info = env.reset(seed=args.seed)
        print(f"observation_shape: {observation.shape}")
        print(f"action_space: {env.action_space}")
        print(f"controlled_agent_id: {info['controlled_agent_id']}")
        print(f"controlled_team_id: {info['controlled_team_id']}")
        print(f"scenario_id: {info['scenario_id']}")
        print(f"ally_agent_ids: {info['ally_agent_ids']}")
        print(f"enemy_agent_ids: {info['enemy_agent_ids']}")

        for episode in range(args.episodes):
            if episode > 0:
                observation, _ = env.reset(seed=args.seed + episode)
            episode_reward = 0.0
            for _ in range(args.max_steps):
                if not np.isfinite(observation).all():
                    nan_count += 1
                action = int(rng.integers(0, env.action_space.n))
                observation, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                final_tick = int(info["tick"])
                if terminated or truncated:
                    terminated_count += int(terminated)
                    truncated_count += int(truncated)
                    break
            total_reward += episode_reward

        if not np.isfinite(observation).all():
            nan_count += 1
    finally:
        env.close()

    if not math.isfinite(total_reward):
        print("finite_total_reward: false")
        return 1

    print(f"episodes: {args.episodes}")
    print(f"max_steps: {args.max_steps}")
    print(f"seed: {args.seed}")
    print(f"total_reward: {total_reward:.6f}")
    print(f"terminated_count: {terminated_count}")
    print(f"truncated_count: {truncated_count}")
    print(f"final_tick: {final_tick}")
    print(f"team0_alive: {info.get('team0_alive')}")
    print(f"team1_alive: {info.get('team1_alive')}")
    print(f"ally_alive_count: {info.get('ally_alive_count')}")
    print(f"enemy_alive_count: {info.get('enemy_alive_count')}")
    print(f"no_nan: {str(nan_count == 0).lower()}")
    return 0 if nan_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
