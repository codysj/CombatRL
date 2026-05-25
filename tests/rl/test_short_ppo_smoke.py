from pathlib import Path

import pytest
import yaml

from combatrl.replay.validators import validate_replay
from combatrl.training.train_ppo import train_ppo


@pytest.mark.slow
def test_short_ppo_smoke_creates_checkpoint_metadata_metrics_and_replay(
    tmp_path: Path,
) -> None:
    config_path = _tiny_training_config(tmp_path)

    run_dir = train_ppo(config_path, smoke=True)

    assert (run_dir / "model_final.zip").exists()
    assert (run_dir / "config.yaml").exists()
    assert (run_dir / "model_metadata.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "evaluation_metrics.json").exists()

    metrics = yaml.safe_load((run_dir / "metrics.json").read_text(encoding="utf-8"))
    replay_path = Path(metrics["evaluation"]["sample_replay_path"])
    assert replay_path.exists()
    validate_replay(replay_path)


def _tiny_training_config(tmp_path: Path) -> Path:
    payload = yaml.safe_load(
        Path("configs/training/ppo_1v1_baseline.yaml").read_text(encoding="utf-8")
    )
    payload.update(
        {
            "output_dir": str(tmp_path / "checkpoints"),
            "tensorboard_log": str(tmp_path / "tensorboard"),
            "total_timesteps": 128,
            "smoke_total_timesteps": 128,
            "n_envs": 1,
            "n_steps": 32,
            "batch_size": 32,
            "n_epochs": 1,
            "eval_freq": 64,
            "eval_episodes": 1,
            "checkpoint_freq": 64,
            "save_sample_replay": True,
        }
    )
    config_path = tmp_path / "ppo_smoke.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path
