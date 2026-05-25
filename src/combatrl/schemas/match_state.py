"""Match state schema for the authoritative simulator state."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from combatrl.schemas.agent_state import AgentState


class ObstacleState(BaseModel):
    """Minimal rectangular obstacle state for P1."""

    model_config = ConfigDict(extra="forbid")

    obstacle_id: str
    x: float
    y: float
    width: float = Field(gt=0.0)
    height: float = Field(gt=0.0)


class MatchState(BaseModel):
    """Top-level mutable simulator state."""

    model_config = ConfigDict(extra="forbid")

    match_id: str
    seed: int
    tick: int = Field(ge=0)
    max_ticks: int = Field(gt=0)
    tick_rate_hz: int = Field(gt=0)
    arena_width: float = Field(gt=0.0)
    arena_height: float = Field(gt=0.0)
    agents: dict[str, AgentState]
    obstacles: list[ObstacleState]
    terminal: bool
    winner_team_id: int | None
    terminal_reason: str | None

    @model_validator(mode="after")
    def validate_match_state(self) -> "MatchState":
        if self.tick > self.max_ticks:
            msg = "tick must be less than or equal to max_ticks"
            raise ValueError(msg)

        for agent_id, agent in self.agents.items():
            if agent_id != agent.agent_id:
                msg = f"agents key {agent_id!r} does not match agent_id {agent.agent_id!r}"
                raise ValueError(msg)

        if self.terminal and self.terminal_reason is None:
            msg = "terminal state requires terminal_reason"
            raise ValueError(msg)

        if self.terminal_reason == "timeout" and self.winner_team_id is not None:
            msg = "timeout terminal states must not have a winner"
            raise ValueError(msg)

        return self
