from pathlib import Path

import pytest
import yaml

from combatrl.training.train_ppo import train_ppo


@pytest.mark.slow
def test_2v2_ppo_smoke_completes(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        Path("configs/training/ppo_2v2_baseline.yaml").read_text(encoding="utf-8")
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
            "save_sample_replay": False,
        }
    )
    config_path = tmp_path / "ppo_2v2_smoke.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    run_dir = train_ppo(config_path, smoke=True)

    assert (run_dir / "model_final.zip").exists()
    assert (run_dir / "evaluation_metrics.json").exists()
