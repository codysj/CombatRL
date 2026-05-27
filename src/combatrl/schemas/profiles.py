"""Behavior profile schema."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from combatrl.core.constants import PROFILE_SCHEMA_VERSION


class BehaviorProfile(BaseModel):
    """Bounded numeric control object for inference-time behavior modulation."""

    model_config = ConfigDict(extra="forbid")

    profile_schema_version: str = PROFILE_SCHEMA_VERSION
    profile_id: str
    aggression: float = Field(ge=0.0, le=1.0)
    caution: float = Field(ge=0.0, le=1.0)
    cohesion: float = Field(ge=0.0, le=1.0)
    protectiveness: float = Field(ge=0.0, le=1.0)
    focus_fire: float = Field(ge=0.0, le=1.0)
    greed: float = Field(ge=0.0, le=1.0)
    spacing: float = Field(ge=0.0, le=1.0)
    objective_bias: float = Field(ge=0.0, le=1.0)
    notes: str | None = None

    @field_validator("profile_schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if value != PROFILE_SCHEMA_VERSION:
            msg = f"profile_schema_version must be {PROFILE_SCHEMA_VERSION}"
            raise ValueError(msg)
        return value

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, value: str) -> str:
        if not value.strip():
            msg = "profile_id must be non-empty"
            raise ValueError(msg)
        return value
