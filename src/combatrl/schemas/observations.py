"""Observation vector schemas for RL environments."""

import math

from pydantic import BaseModel, ConfigDict, model_validator


class ObservationVector(BaseModel):
    """Versioned fixed-layout numeric observation vector."""

    model_config = ConfigDict(extra="forbid")

    observation_schema_version: str
    agent_id: str
    values: list[float]
    feature_names: list[str]

    @model_validator(mode="after")
    def validate_observation(self) -> "ObservationVector":
        if len(self.values) != len(self.feature_names):
            msg = "values and feature_names must have the same length"
            raise ValueError(msg)
        if not all(math.isfinite(value) for value in self.values):
            msg = "observation values must be finite"
            raise ValueError(msg)
        return self
