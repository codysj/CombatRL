"""Reward schemas for RL environments."""

import math

from pydantic import BaseModel, ConfigDict, Field, model_validator

REQUIRED_REWARD_COMPONENTS: tuple[str, ...] = (
    "win_bonus",
    "loss_penalty",
    "damage_dealt",
    "damage_taken_penalty",
    "death_penalty",
    "ally_death_penalty",
    "invalid_action_penalty",
    "time_penalty",
)


class RewardBreakdown(BaseModel):
    """Per-step reward components for one controlled agent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    tick: int = Field(ge=0)
    total_reward: float
    components: dict[str, float]

    @model_validator(mode="after")
    def validate_reward(self) -> "RewardBreakdown":
        missing = set(REQUIRED_REWARD_COMPONENTS) - set(self.components)
        if missing:
            msg = f"missing reward component keys: {sorted(missing)}"
            raise ValueError(msg)
        if not math.isfinite(self.total_reward):
            msg = "total_reward must be finite"
            raise ValueError(msg)
        if not all(math.isfinite(value) for value in self.components.values()):
            msg = "reward component values must be finite"
            raise ValueError(msg)
        component_total = sum(self.components.values())
        if not math.isclose(component_total, self.total_reward, rel_tol=1e-9, abs_tol=1e-9):
            msg = "sum of reward components must equal total_reward"
            raise ValueError(msg)
        return self
