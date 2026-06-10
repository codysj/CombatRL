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

    # --- new degenerate-policy detection keys ---
    assert "action_histogram" in metrics
    assert "action_rates" in metrics
    assert "no_op_rate" in metrics
    assert "attack_action_rate" in metrics
    assert "movement_action_rate" in metrics

    # Histogram counts must sum to total_steps (episode length).
    total_steps = sum(metrics["action_histogram"].values())
    episode_length = int(round(metrics["mean_episode_length"]))
    # When num_episodes=1 the sum must equal the single episode length.
    assert total_steps == episode_length, (
        f"histogram sum {total_steps} != episode length {episode_length}"
    )

    # Rates must sum to ~1.0 (within floating-point tolerance).
    rate_sum = sum(metrics["action_rates"].values())
    assert abs(rate_sum - 1.0) < 1e-6, f"action_rates sum {rate_sum} != 1.0"

    # Summary rates are floats in [0, 1].
    for key in ("no_op_rate", "attack_action_rate", "movement_action_rate"):
        val = float(metrics[key])
        assert 0.0 <= val <= 1.0, f"{key}={val} out of range"

    # no_op + attack + movement must equal the full rate sum (~1.0).
    combined = (
        metrics["no_op_rate"] + metrics["attack_action_rate"] + metrics["movement_action_rate"]
    )
    assert abs(combined - 1.0) < 1e-6, f"combined summary rates {combined} != 1.0"


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
