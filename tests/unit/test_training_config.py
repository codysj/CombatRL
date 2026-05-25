from pathlib import Path

import pytest

from combatrl.training.configs import PPOTrainingConfig, load_training_config

CONFIG_PATH = Path("configs/training/ppo_1v1_baseline.yaml")


def test_loads_default_ppo_training_config() -> None:
    config = load_training_config(CONFIG_PATH)

    assert config.algorithm == "PPO"
    assert config.policy == "MlpPolicy"
    assert config.env_config_path == "configs/env/gym_1v1_ranged_vs_random.yaml"
    assert config.n_envs == 4
    assert config.smoke_total_timesteps <= config.total_timesteps


def test_loads_2v2_ppo_training_config() -> None:
    config = load_training_config("configs/training/ppo_2v2_baseline.yaml")

    assert config.run_name == "ppo_2v2_baseline"
    assert config.env_config_path == "configs/env/gym_2v2_controlled_ranged.yaml"
    assert config.smoke_total_timesteps <= config.total_timesteps


def test_rejects_invalid_n_envs() -> None:
    config = load_training_config(CONFIG_PATH).model_dump(mode="json")
    config["n_envs"] = 0

    with pytest.raises(ValueError, match="n_envs"):
        PPOTrainingConfig.model_validate(config)


def test_rejects_smoke_timesteps_above_total() -> None:
    config = load_training_config(CONFIG_PATH).model_dump(mode="json")
    config["smoke_total_timesteps"] = config["total_timesteps"] + 1

    with pytest.raises(ValueError, match="smoke_total_timesteps"):
        PPOTrainingConfig.model_validate(config)
