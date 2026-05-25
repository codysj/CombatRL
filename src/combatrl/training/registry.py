"""Local file-based checkpoint metadata registry."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from combatrl import __version__ as combatrl_version
from combatrl.core.constants import ACTION_SCHEMA_VERSION, OBSERVATION_SCHEMA_VERSION


class ModelMetadata(BaseModel):
    """Metadata stored next to an SB3 checkpoint."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str
    algorithm: str
    checkpoint_path: str
    env_config_path: str
    training_config_path: str
    observation_schema_version: str
    action_schema_version: str
    total_timesteps: int
    seed: int
    created_at_utc: str
    sb3_version: str | None
    combatrl_version: str
    notes: str | None = None


def write_model_metadata(
    metadata_path: str | Path,
    *,
    policy_id: str,
    algorithm: str,
    checkpoint_path: str | Path,
    env_config_path: str | Path,
    training_config_path: str | Path,
    total_timesteps: int,
    seed: int,
    notes: str | None = None,
) -> ModelMetadata:
    """Write checkpoint metadata as JSON and return the validated model."""
    sb3_version = _sb3_version()
    metadata = ModelMetadata(
        policy_id=policy_id,
        algorithm=algorithm,
        checkpoint_path=str(checkpoint_path),
        env_config_path=str(env_config_path),
        training_config_path=str(training_config_path),
        observation_schema_version=OBSERVATION_SCHEMA_VERSION,
        action_schema_version=ACTION_SCHEMA_VERSION,
        total_timesteps=total_timesteps,
        seed=seed,
        created_at_utc=datetime.now(UTC).isoformat(),
        sb3_version=sb3_version,
        combatrl_version=combatrl_version,
        notes=notes,
    )
    path = Path(metadata_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metadata.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def load_model_metadata(path: str | Path) -> ModelMetadata:
    """Load and validate local checkpoint metadata JSON."""
    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return ModelMetadata.model_validate(payload)


def _sb3_version() -> str | None:
    try:
        import stable_baselines3
    except ImportError:
        return None
    return str(stable_baselines3.__version__)
