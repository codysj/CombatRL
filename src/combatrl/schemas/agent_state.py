"""Agent state schema for the authoritative simulator state."""

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RoleName = Literal["tank", "ranged_dps", "support"]


class AgentState(BaseModel):
    """Mutable per-agent simulator state."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    team_id: int
    role: RoleName
    position: tuple[float, float]
    velocity: tuple[float, float]
    hp: float
    max_hp: float = Field(gt=0.0)
    alive: bool
    movement_speed: float = Field(gt=0.0)
    attack_range: float = Field(gt=0.0)
    attack_damage: float = Field(ge=0.0)
    attack_cooldown_ticks: int = Field(ge=0)
    attack_cooldown_max_ticks: int = Field(gt=0)
    ability_cooldown_ticks: int = Field(ge=0)
    facing_vector: tuple[float, float]
    status_effects: list[str]
    current_target_id: str | None
    last_action_id: int | None

    @field_validator("position", "velocity", "facing_vector")
    @classmethod
    def validate_finite_vector(cls, value: tuple[float, float]) -> tuple[float, float]:
        if not math.isfinite(value[0]) or not math.isfinite(value[1]):
            msg = "vector values must be finite"
            raise ValueError(msg)
        return value

    @field_validator("hp", "max_hp", "movement_speed", "attack_range", "attack_damage")
    @classmethod
    def validate_finite_float(cls, value: float) -> float:
        if not math.isfinite(value):
            msg = "numeric values must be finite"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_hp_and_alive(self) -> "AgentState":
        if self.hp < 0.0 or self.hp > self.max_hp:
            msg = "hp must be in the inclusive range [0, max_hp]"
            raise ValueError(msg)
        if self.alive != (self.hp > 0.0):
            msg = "alive must equal hp > 0"
            raise ValueError(msg)
        return self
