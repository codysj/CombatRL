"""Stable-Baselines3 callback construction for PPO training."""

from pathlib import Path

from stable_baselines3.common.callbacks import (
    BaseCallback,
    CallbackList,
    CheckpointCallback,
    EvalCallback,
)
from stable_baselines3.common.vec_env import VecEnv

from combatrl.training.configs import PPOTrainingConfig


def build_callbacks(
    config: PPOTrainingConfig,
    run_dir: str | Path,
    eval_env: VecEnv,
) -> BaseCallback:
    """Build the PPO callback list using SB3 built-ins."""
    run_path = Path(run_dir)
    eval_dir = run_path / "evaluations"
    checkpoint_dir = run_path / "checkpoints"
    eval_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    return CallbackList(
        [
            EvalCallback(
                eval_env,
                best_model_save_path=str(run_path),
                log_path=str(eval_dir),
                eval_freq=max(config.eval_freq // max(config.n_envs, 1), 1),
                n_eval_episodes=config.eval_episodes,
                deterministic=config.deterministic_eval,
                render=False,
            ),
            CheckpointCallback(
                save_freq=max(config.checkpoint_freq // max(config.n_envs, 1), 1),
                save_path=str(checkpoint_dir),
                name_prefix="ppo_checkpoint",
            ),
        ]
    )
