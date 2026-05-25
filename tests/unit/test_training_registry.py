from pathlib import Path

from combatrl.training.registry import load_model_metadata, write_model_metadata


def test_write_and_load_model_metadata(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "model_final.zip"
    checkpoint_path.write_text("placeholder", encoding="utf-8")
    metadata_path = tmp_path / "model_metadata.json"

    written = write_model_metadata(
        metadata_path,
        policy_id="ppo_1v1_baseline",
        algorithm="PPO",
        checkpoint_path=checkpoint_path,
        env_config_path="configs/env/gym_1v1_ranged_vs_random.yaml",
        training_config_path="configs/training/ppo_1v1_baseline.yaml",
        total_timesteps=128,
        seed=42,
    )
    loaded = load_model_metadata(metadata_path)

    assert loaded == written
    assert loaded.checkpoint_path == str(checkpoint_path)
    assert loaded.algorithm == "PPO"
