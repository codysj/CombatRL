"""Stable-Baselines3 PPO training entry point."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from stable_baselines3 import PPO

from combatrl.training.callbacks import build_callbacks
from combatrl.training.configs import PPOTrainingConfig, load_training_config
from combatrl.training.evaluate_checkpoint import evaluate_checkpoint
from combatrl.training.registry import write_model_metadata
from combatrl.training.vec_env import make_vec_envs


def train_ppo(config_path: str | Path, smoke: bool = False) -> Path:
    """Train the first CombatRL PPO baseline and return the run directory."""
    source_config_path = Path(config_path)
    config = load_training_config(source_config_path)
    total_timesteps = config.smoke_total_timesteps if smoke else config.total_timesteps
    run_dir = _create_run_dir(config)
    resolved_config_path = run_dir / "config.yaml"
    _write_resolved_config(config, resolved_config_path)

    train_env = make_vec_envs(config, eval_mode=False)
    eval_env = make_vec_envs(config, eval_mode=True)
    try:
        model = PPO(
            config.policy,
            train_env,
            seed=config.seed,
            n_steps=config.n_steps,
            batch_size=config.batch_size,
            n_epochs=config.n_epochs,
            gamma=config.gamma,
            gae_lambda=config.gae_lambda,
            learning_rate=config.learning_rate,
            clip_range=config.clip_range,
            ent_coef=config.ent_coef,
            vf_coef=config.vf_coef,
            max_grad_norm=config.max_grad_norm,
            tensorboard_log=str(config.tensorboard_log) if config.tensorboard_log else None,
            verbose=0,
            device="cpu",
        )
        callbacks = build_callbacks(config, run_dir, eval_env)
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            tb_log_name=config.run_name,
            progress_bar=False,
        )
        final_model_path = run_dir / "model_final.zip"
        model.save(final_model_path)
        _copy_best_model_if_available(run_dir)
        _write_eval_history_csv(run_dir)
        evaluation = evaluate_checkpoint(
            final_model_path,
            config.env_config_path,
            num_episodes=_smoke_eval_episodes(config) if smoke else config.eval_episodes,
            seed_start=config.sample_replay_seed,
            deterministic=config.deterministic_eval,
            save_replay=config.save_sample_replay,
            replay_output_dir=run_dir / "sample_replays",
        )
        metrics = {
            "run_dir": str(run_dir),
            "training_config_path": str(resolved_config_path),
            "source_training_config_path": str(source_config_path),
            "final_model_path": str(final_model_path),
            "best_model_path": str(run_dir / "best_model.zip")
            if (run_dir / "best_model.zip").exists()
            else None,
            "total_timesteps": total_timesteps,
            "smoke": smoke,
            "evaluation": evaluation,
        }
        _write_json(run_dir / "metrics.json", metrics)
        write_model_metadata(
            run_dir / "model_metadata.json",
            policy_id=config.run_name,
            algorithm=config.algorithm,
            checkpoint_path=final_model_path,
            env_config_path=config.env_config_path,
            training_config_path=resolved_config_path,
            total_timesteps=total_timesteps,
            seed=config.seed,
            notes="Smoke run" if smoke else "PPO baseline run",
        )
        return run_dir
    finally:
        train_env.close()
        eval_env.close()


def _create_run_dir(config: PPOTrainingConfig) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(config.output_dir) / f"run_{timestamp}"
    suffix = 1
    while run_dir.exists():
        run_dir = Path(config.output_dir) / f"run_{timestamp}_{suffix}"
        suffix += 1
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _write_resolved_config(config: PPOTrainingConfig, output_path: Path) -> None:
    payload = config.model_dump(mode="json")
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _copy_best_model_if_available(run_dir: Path) -> None:
    sb3_best_model = run_dir / "best_model.zip"
    if not sb3_best_model.exists():
        return
    canonical_best_model = run_dir / "best_model.zip"
    if sb3_best_model != canonical_best_model:
        shutil.copy2(sb3_best_model, canonical_best_model)


def _write_eval_history_csv(run_dir: Path) -> None:
    npz_path = run_dir / "evaluations.npz"
    nested_npz_path = run_dir / "evaluations" / "evaluations.npz"
    if not npz_path.exists() and nested_npz_path.exists():
        npz_path = nested_npz_path
    if not npz_path.exists():
        return

    data = np.load(npz_path)
    timesteps = data.get("timesteps", [])
    results = data.get("results", [])
    lengths = data.get("ep_lengths", [])
    lines = ["timesteps,mean_reward,std_reward,mean_episode_length\n"]
    for index, timestep in enumerate(timesteps):
        rewards = results[index] if index < len(results) else []
        episode_lengths = lengths[index] if index < len(lengths) else []
        lines.append(
            f"{int(timestep)},{float(np.mean(rewards))},{float(np.std(rewards))},"
            f"{float(np.mean(episode_lengths))}\n"
        )
    (run_dir / "eval_history.csv").write_text("".join(lines), encoding="utf-8")


def _smoke_eval_episodes(config: PPOTrainingConfig) -> int:
    return min(config.eval_episodes, 3)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
