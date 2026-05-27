"""Evaluation schema models for fixed-seed policy comparisons."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PolicyType = Literal["heuristic", "ppo_checkpoint", "random", "profiled"]


class PolicySpec(BaseModel):
    """A policy or policy wrapper evaluated by the benchmark suite."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str
    policy_type: PolicyType
    checkpoint_path: str | None = None
    base_policy_id: str | None = None
    profile_id: str | None = None
    controlled_agent_id: str | None = None
    notes: str | None = None


class ScenarioSpec(BaseModel):
    """A fixed scenario/environment definition for evaluation."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    simulation_config_path: str
    env_config_path: str | None = None
    controlled_agent_id: str
    teammate_policy_id: str | None = None
    opponent_policy_ids: list[str]
    description: str | None = None


MetricValue = float | int | str | None


class MatchEvaluationRecord(BaseModel):
    """Metrics and metadata for one seeded match."""

    model_config = ConfigDict(extra="forbid")

    evaluation_id: str
    match_id: str
    scenario_id: str
    seed: int = Field(ge=0)
    policy_id: str
    opponent_id: str
    profile_id: str | None
    replay_path: str | None
    terminal_reason: str | None
    winner_team_id: int | None
    controlled_team_id: int
    metrics: dict[str, MetricValue]

    @field_validator("metrics")
    @classmethod
    def validate_metric_values(cls, value: dict[str, MetricValue]) -> dict[str, MetricValue]:
        for metric_name, metric_value in value.items():
            if isinstance(metric_value, float) and not math.isfinite(metric_value):
                msg = f"metric {metric_name!r} must be finite"
                raise ValueError(msg)
        return value


class EvaluationResult(BaseModel):
    """Aggregate result for one scenario/policy/opponent evaluation."""

    model_config = ConfigDict(extra="forbid")

    metrics_schema_version: str
    evaluation_id: str
    scenario_id: str
    policy_id: str
    opponent_id: str
    profile_id: str | None
    num_matches: int = Field(gt=0)
    seed_start: int = Field(ge=0)
    aggregate_metrics: dict[str, float]
    per_match_metrics_path: str
    replay_sample_paths: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result(self) -> EvaluationResult:
        if not self.metrics_schema_version:
            msg = "metrics_schema_version must be explicit"
            raise ValueError(msg)
        _validate_numeric_mapping(self.aggregate_metrics, field_name="aggregate_metrics")
        return self


def _validate_numeric_mapping(values: dict[str, Any], *, field_name: str) -> None:
    for metric_name, metric_value in values.items():
        if not isinstance(metric_value, int | float):
            msg = f"{field_name}.{metric_name} must be numeric"
            raise ValueError(msg)
        if not math.isfinite(float(metric_value)):
            msg = f"{field_name}.{metric_name} must be finite"
            raise ValueError(msg)
