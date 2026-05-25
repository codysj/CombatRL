"""Versioned replay schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from combatrl.core.constants import REPLAY_SCHEMA_VERSION
from combatrl.schemas.agent_state import AgentState


class EventLog(BaseModel):
    """One deterministic event emitted during match resolution."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    tick: int = Field(ge=0)
    event_type: str
    source_agent_id: str | None
    target_agent_id: str | None
    payload: dict[str, Any]


class ReplayFrame(BaseModel):
    """Serializable snapshot of a replay tick."""

    model_config = ConfigDict(extra="forbid")

    replay_schema_version: str
    match_id: str
    tick: int = Field(ge=0)
    sim_time_seconds: float = Field(ge=0.0)
    agents: list[AgentState]
    events: list[EventLog]
    scoreboard: dict[str, float | int | str | None]

    @field_validator("replay_schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if value != REPLAY_SCHEMA_VERSION:
            msg = f"replay_schema_version must be {REPLAY_SCHEMA_VERSION}"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_frame(self) -> "ReplayFrame":
        agent_ids = [agent.agent_id for agent in self.agents]
        if agent_ids != sorted(agent_ids):
            msg = "agents must be sorted by agent_id"
            raise ValueError(msg)

        bad_event_ticks = [event.event_id for event in self.events if event.tick != self.tick]
        if bad_event_ticks:
            msg = f"frame events must match frame tick {self.tick}: {bad_event_ticks}"
            raise ValueError(msg)

        return self


class ReplayMetadata(BaseModel):
    """Replay metadata written once at match start."""

    model_config = ConfigDict(extra="forbid")

    replay_schema_version: str
    match_id: str
    scenario_id: str
    seed: int
    config: dict[str, Any]
    config_hash: str
    tick_rate_hz: int = Field(gt=0)
    decision_rate_hz: int | None
    created_at_utc: str
    combatrl_version: str

    @field_validator("replay_schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if value != REPLAY_SCHEMA_VERSION:
            msg = f"replay_schema_version must be {REPLAY_SCHEMA_VERSION}"
            raise ValueError(msg)
        return value


class ReplaySummary(BaseModel):
    """Compact replay terminal summary."""

    model_config = ConfigDict(extra="forbid")

    replay_schema_version: str
    match_id: str
    scenario_id: str
    seed: int
    final_tick: int = Field(ge=0)
    terminal: bool
    terminal_reason: str | None
    winner_team_id: int | None
    frame_count: int = Field(ge=0)
    event_count: int = Field(ge=0)
    team0_alive: int = Field(ge=0)
    team1_alive: int = Field(ge=0)
    team0_total_hp: float = Field(ge=0.0)
    team1_total_hp: float = Field(ge=0.0)

    @field_validator("replay_schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if value != REPLAY_SCHEMA_VERSION:
            msg = f"replay_schema_version must be {REPLAY_SCHEMA_VERSION}"
            raise ValueError(msg)
        return value


def make_event_log(
    *,
    match_id: str,
    tick: int,
    index: int,
    event_type: str,
    source_agent_id: str | None = None,
    target_agent_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> EventLog:
    """Create a deterministic event ID and validated event model."""
    return EventLog(
        event_id=f"{match_id}:tick-{tick}:event-{index}",
        tick=tick,
        event_type=event_type,
        source_agent_id=source_agent_id,
        target_agent_id=target_agent_id,
        payload={} if payload is None else payload,
    )
