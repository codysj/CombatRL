"""Vectorized environment factories for SB3 training."""

from collections.abc import Callable
from pathlib import Path

import gymnasium as gym
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from combatrl.envs import CombatRLGymEnv
from combatrl.schemas.configs import load_environment_config
from combatrl.training.configs import PPOTrainingConfig


def make_env(env_config_path: str | Path, seed: int, rank: int = 0) -> Callable[[], gym.Env]:
    """Build one seeded, headless Gymnasium env thunk for SB3."""

    def _init() -> gym.Env:
        env_config = load_environment_config(env_config_path).model_copy(
            update={
                "capture_replays": False,
                "replay_sample_rate": 0.0,
                "seed": seed + rank,
            }
        )
        env = CombatRLGymEnv(env_config, render_mode=None)
        env.reset(seed=seed + rank)
        return Monitor(env)

    return _init


def make_vec_envs(config: PPOTrainingConfig, eval_mode: bool = False) -> DummyVecEnv:
    """Create DummyVecEnv instances with unique per-env seeds."""
    n_envs = 1 if eval_mode else config.n_envs
    seed_offset = 10_000 if eval_mode else 0
    env_fns = [
        make_env(config.env_config_path, seed=config.seed + seed_offset, rank=rank)
        for rank in range(n_envs)
    ]
    return DummyVecEnv(env_fns)
