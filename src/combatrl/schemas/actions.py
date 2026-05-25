"""Discrete simulator action schemas."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ActionType(StrEnum):
    """Simple discrete action set for Phase P2."""

    NO_OP = "NO_OP"
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    MOVE_UP_LEFT = "MOVE_UP_LEFT"
    MOVE_UP_RIGHT = "MOVE_UP_RIGHT"
    MOVE_DOWN_LEFT = "MOVE_DOWN_LEFT"
    MOVE_DOWN_RIGHT = "MOVE_DOWN_RIGHT"
    ATTACK_NEAREST = "ATTACK_NEAREST"


class ActionCommand(BaseModel):
    """One action issued to one agent for a simulator tick."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    action_type: ActionType
