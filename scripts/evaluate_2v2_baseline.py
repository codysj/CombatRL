"""Run lightweight deterministic 2v2 baseline evaluation episodes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from combatrl.agents.registry import create_policy
from combatrl.envs import CombatRLGymEnv
from combatrl.schemas.match_state import MatchState

DEFAULT_ENV_CONFIG = Path("configs/env/gym_2v2_controlled_ranged.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate random or scripted 2v2 env episodes.")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--policy", choices=["random", "scripted"], default="random")
    parser.add_argument("--scripted-policy-id", default="aggressive")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = evaluate(args)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


def evaluate(args: argparse.Namespace) -> dict[str, float | int | str]:
    env = CombatRLGymEnv(args.env_config, render_mode=None)
    rng = np.random.default_rng(args.seed)
    controlled_team_id = _controlled_team_id(env)
    rewards: list[float] = []
    lengths: list[int] = []
    wins = 0
    timeouts = 0
    controlled_alive = 0
    ally_alive = 0
    invalid_actions = 0
    total_steps = 0
    try:
        for episode_index in range(args.episodes):
            scripted_policy = create_policy(args.scripted_policy_id, seed=args.seed + episode_index)
            scripted_policy.reset(args.seed + episode_index)
            observation, _ = env.reset(seed=args.seed + episode_index)
            del observation
            episode_reward = 0.0
            episode_length = 0
            terminated = False
            truncated = False
            final_info = {}
            while not (terminated or truncated):
                state = _require_state(env)
                if args.policy == "scripted":
                    command = scripted_policy.select_action(
                        state,
                        env.env_config.controlled_agent_id,
                    )
                    action = env.action_codec.encode(command.action_type)
                else:
                    mask = env.action_codec.valid_action_mask(
                        state,
                        env.env_config.controlled_agent_id,
                    )
                    action = int(rng.choice(np.flatnonzero(mask)))
                _, reward, terminated, truncated, final_info = env.step(action)
                episode_reward += float(reward)
                episode_length += 1
                total_steps += 1
                invalid_actions += int(bool(final_info.get("invalid_action", False)))

            rewards.append(episode_reward)
            lengths.append(episode_length)
            wins += int(final_info.get("winner_team_id") == controlled_team_id)
            timeouts += int(final_info.get("terminal_reason") == "max_ticks")
            controlled_alive += int(bool(final_info.get("controlled_agent_alive", False)))
            ally_alive += int(int(final_info.get("ally_alive_count", 0)) > 0)
    finally:
        env.close()

    episodes = max(args.episodes, 1)
    return {
        "env_config_path": str(args.env_config),
        "episodes": args.episodes,
        "seed": args.seed,
        "policy": args.policy,
        "win_rate": wins / episodes,
        "timeout_rate": timeouts / episodes,
        "mean_episode_reward": float(np.mean(rewards)) if rewards else 0.0,
        "mean_episode_length": float(np.mean(lengths)) if lengths else 0.0,
        "controlled_survival_rate": controlled_alive / episodes,
        "ally_survival_rate": ally_alive / episodes,
        "invalid_action_rate": invalid_actions / max(total_steps, 1),
    }


def _controlled_team_id(env: CombatRLGymEnv) -> int:
    for team in env.simulation_config.teams:
        for agent in team.agents:
            if agent.agent_id == env.env_config.controlled_agent_id:
                return agent.team_id
    msg = f"controlled agent not found: {env.env_config.controlled_agent_id}"
    raise ValueError(msg)


def _require_state(env: CombatRLGymEnv) -> MatchState:
    if env._engine is None:  # noqa: SLF001
        msg = "environment simulator is not initialized"
        raise RuntimeError(msg)
    return env._engine.state  # noqa: SLF001


if __name__ == "__main__":
    raise SystemExit(main())
