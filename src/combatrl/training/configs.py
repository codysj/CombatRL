"""Training configuration schemas and loaders."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PPOTrainingConfig(BaseModel):
    """Validated Stable-Baselines3 PPO training configuration."""

    model_config = ConfigDict(extra="forbid")

    algorithm: str = "PPO"
    policy: str = "MlpPolicy"
    env_config_path: str | Path
    run_name: str = "ppo_1v1_baseline"
    seed: int = 42
    total_timesteps: int = Field(gt=0)
    smoke_total_timesteps: int = Field(gt=0)
    n_envs: int = Field(gt=0)
    n_steps: int = Field(gt=0)
    batch_size: int = Field(gt=0)
    n_epochs: int = Field(gt=0)
    gamma: float = Field(gt=0.0, le=1.0)
    gae_lambda: float = Field(gt=0.0, le=1.0)
    learning_rate: float = Field(gt=0.0)
    clip_range: float = Field(gt=0.0)
    ent_coef: float = Field(ge=0.0)
    vf_coef: float = Field(ge=0.0)
    max_grad_norm: float = Field(gt=0.0)
    eval_freq: int = Field(gt=0)
    eval_episodes: int = Field(gt=0)
    checkpoint_freq: int = Field(gt=0)
    tensorboard_log: str | Path | None = None
    output_dir: str | Path
    save_sample_replay: bool = True
    sample_replay_seed: int = 123
    deterministic_eval: bool = True
    init_checkpoint: str | Path | None = None

    @model_validator(mode="after")
    def validate_init_checkpoint(self) -> "PPOTrainingConfig":
        """Fail fast when a configured warm-start checkpoint does not exist."""
        if self.init_checkpoint is not None and not Path(self.init_checkpoint).exists():
            msg = f"init_checkpoint does not exist: {self.init_checkpoint}"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_ppo_config(self) -> "PPOTrainingConfig":
        """Validate cross-field constraints."""
        if self.algorithm != "PPO":
            msg = "algorithm must be PPO for PPOTrainingConfig"
            raise ValueError(msg)
        if self.smoke_total_timesteps > self.total_timesteps:
            msg = "smoke_total_timesteps must be less than or equal to total_timesteps"
            raise ValueError(msg)
        return self


def load_training_config(path: str | Path) -> PPOTrainingConfig:
    """Load and validate a PPO training config from YAML."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    if raw_config is None:
        msg = f"training configuration file is empty: {config_path}"
        raise ValueError(msg)

    return PPOTrainingConfig.model_validate(raw_config)
