import math
from pathlib import Path

import pytest
import yaml

from combatrl.training.evaluate_checkpoint import evaluate_checkpoint
from combatrl.training.train_ppo import train_ppo


@pytest.mark.slow
def test_evaluate_checkpoint_returns_finite_metrics(tmp_path: Path) -> None:
    config_path = _tiny_training_config(tmp_path)
    run_dir = train_ppo(config_path, smoke=True)

    metrics = evaluate_checkpoint(
        run_dir / "model_final.zip",
        "configs/env/gym_1v1_ranged_vs_random.yaml",
        num_episodes=1,
        seed_start=2000,
        deterministic=True,
    )

    for key in ("mean_reward", "win_rate", "timeout_rate", "mean_episode_length"):
        assert key in metrics
        assert math.isfinite(float(metrics[key]))
    assert Path(metrics["metrics_path"]).exists()


def _tiny_training_config(tmp_path: Path) -> Path:
    payload = yaml.safe_load(
        Path("configs/training/ppo_1v1_baseline.yaml").read_text(encoding="utf-8")
    )
    payload.update(
        {
            "output_dir": str(tmp_path / "checkpoints"),
            "tensorboard_log": str(tmp_path / "tensorboard"),
            "total_timesteps": 64,
            "smoke_total_timesteps": 64,
            "n_envs": 1,
            "n_steps": 32,
            "batch_size": 32,
            "n_epochs": 1,
            "eval_freq": 64,
            "eval_episodes": 1,
            "checkpoint_freq": 64,
            "save_sample_replay": False,
        }
    )
    config_path = tmp_path / "ppo_smoke_eval.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path
