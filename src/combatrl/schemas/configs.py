"""Simulation configuration schemas and loading helpers."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from combatrl.core.constants import CONFIG_SCHEMA_VERSION

RoleName = Literal["tank", "ranged_dps", "support"]
WinCondition = Literal["elimination", "objective_control"]


class TeamAgentConfig(BaseModel):
    """Configuration for one agent slot in a team."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    team_id: int
    role: RoleName
    spawn_position: tuple[float, float]


class TeamConfig(BaseModel):
    """Configuration for one team."""

    model_config = ConfigDict(extra="forbid")

    team_id: int
    agents: list[TeamAgentConfig]

    @model_validator(mode="after")
    def validate_team_id(self) -> "TeamConfig":
        if self.team_id not in {0, 1}:
            msg = "team_id must be 0 or 1 for the MVP"
            raise ValueError(msg)
        for agent in self.agents:
            if agent.team_id != self.team_id:
                msg = "agent team_id must match parent team_id"
                raise ValueError(msg)
        return self


class ObstacleConfig(BaseModel):
    """Axis-aligned rectangular obstacle configuration."""

    model_config = ConfigDict(extra="forbid")

    obstacle_id: str
    x: float
    y: float
    width: float = Field(gt=0.0)
    height: float = Field(gt=0.0)


class SimulationConfig(BaseModel):
    """Top-level simulation configuration."""

    model_config = ConfigDict(extra="forbid")

    config_schema_version: str
    scenario_id: str
    tick_rate_hz: int = Field(gt=0)
    max_ticks: int = Field(gt=0)
    arena_width: float = Field(gt=0.0)
    arena_height: float = Field(gt=0.0)
    teams: list[TeamConfig]
    obstacles: list[ObstacleConfig]
    win_condition: WinCondition

    @model_validator(mode="after")
    def validate_simulation_config(self) -> "SimulationConfig":
        if self.config_schema_version != CONFIG_SCHEMA_VERSION:
            msg = f"config_schema_version must be {CONFIG_SCHEMA_VERSION}"
            raise ValueError(msg)

        team_ids = {team.team_id for team in self.teams}
        if not team_ids.issubset({0, 1}):
            msg = "team IDs must be 0 or 1 for the MVP"
            raise ValueError(msg)

        agent_ids: set[str] = set()
        for team in self.teams:
            for agent in team.agents:
                if agent.agent_id in agent_ids:
                    msg = f"duplicate agent_id: {agent.agent_id}"
                    raise ValueError(msg)
                agent_ids.add(agent.agent_id)

                x, y = agent.spawn_position
                if x < 0.0 or x > self.arena_width or y < 0.0 or y > self.arena_height:
                    msg = f"spawn_position for {agent.agent_id} is outside the arena"
                    raise ValueError(msg)

        return self


def load_simulation_config(path: str | Path) -> SimulationConfig:
    """Load and validate a simulation config from YAML."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    if raw_config is None:
        msg = f"configuration file is empty: {config_path}"
        raise ValueError(msg)

    return SimulationConfig.model_validate(raw_config)


class EnvironmentConfig(BaseModel):
    """Configuration for the single-agent Gymnasium wrapper."""

    model_config = ConfigDict(extra="forbid")

    env_id: str
    simulation_config_path: str | Path
    controlled_agent_id: str
    opponent_policy_ids: list[str]
    teammate_policy_id: str | None = None
    reward_config: dict[str, float] = Field(default_factory=dict)
    observation_schema_version: str
    action_schema_version: str
    capture_replays: bool = False
    replay_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    decision_interval_ticks: int = Field(default=4, gt=0)
    terminate_on_controlled_death: bool = False
    seed: int | None = None


def load_environment_config(path: str | Path) -> EnvironmentConfig:
    """Load and validate a Gymnasium environment config from YAML."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    if raw_config is None:
        msg = f"environment configuration file is empty: {config_path}"
        raise ValueError(msg)

    return EnvironmentConfig.model_validate(raw_config)
