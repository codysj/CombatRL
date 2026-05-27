"""Aggregation helpers for evaluation metrics."""

from __future__ import annotations

import math
import random
from typing import Any

from combatrl.schemas.evaluation import MatchEvaluationRecord

KEY_MIN_MAX_METRICS = {
    "damage_dealt",
    "damage_taken",
    "survival_ticks",
    "final_hp",
    "avg_distance_to_nearest_enemy",
    "avg_distance_to_ally",
    "attack_action_rate",
    "retreat_action_rate",
}


def aggregate_match_records(records: list[MatchEvaluationRecord]) -> dict[str, float]:
    """Aggregate validated per-match records in deterministic seed order."""
    if not records:
        msg = "cannot aggregate empty match record list"
        raise ValueError(msg)
    sorted_records = sorted(records, key=lambda record: (record.seed, record.match_id))
    return aggregate_metric_dicts([record.metrics for record in sorted_records])


def aggregate_metric_dicts(metric_dicts: list[dict[str, Any]]) -> dict[str, float]:
    """Aggregate numeric metric dictionaries with mean/std and outcome rates."""
    if not metric_dicts:
        msg = "cannot aggregate empty metric list"
        raise ValueError(msg)

    numeric_names = sorted(
        {
            metric_name
            for metrics in metric_dicts
            for metric_name, value in metrics.items()
            if _is_numeric(value)
        }
    )
    aggregate = mean_std_for_metrics(metric_dicts, numeric_names)
    aggregate["num_matches"] = float(len(metric_dicts))
    aggregate["win_rate"] = _mean([float(metrics.get("win", 0.0)) for metrics in metric_dicts])
    aggregate["loss_rate"] = _mean([float(metrics.get("loss", 0.0)) for metrics in metric_dicts])
    aggregate["timeout_rate"] = _mean(
        [float(metrics.get("draw_or_timeout", 0.0)) for metrics in metric_dicts]
    )

    for metric_name in sorted(KEY_MIN_MAX_METRICS & set(numeric_names)):
        values = _numeric_values(metric_dicts, metric_name)
        if values:
            aggregate[f"min_{metric_name}"] = min(values)
            aggregate[f"max_{metric_name}"] = max(values)
    return dict(sorted(aggregate.items()))


def mean_std_for_metrics(
    metric_dicts: list[dict[str, Any]],
    metric_names: list[str] | tuple[str, ...],
) -> dict[str, float]:
    """Return mean_<metric> and std_<metric> for numeric values."""
    if not metric_dicts:
        msg = "cannot compute means for empty metric list"
        raise ValueError(msg)
    output: dict[str, float] = {}
    for metric_name in sorted(metric_names):
        values = _numeric_values(metric_dicts, metric_name)
        if not values:
            continue
        output[f"mean_{metric_name}"] = _mean(values)
        output[f"std_{metric_name}"] = _std(values)
    return output


def bootstrap_ci(
    metric_values: list[float],
    num_samples: int = 1000,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Return a deterministic bootstrap confidence interval for the mean."""
    if not metric_values:
        msg = "cannot bootstrap empty metric list"
        raise ValueError(msg)
    if num_samples <= 0:
        msg = "num_samples must be positive"
        raise ValueError(msg)
    if not 0.0 < confidence < 1.0:
        msg = "confidence must be in (0, 1)"
        raise ValueError(msg)

    rng = random.Random(0)
    values = [float(value) for value in metric_values]
    sample_means = []
    for _ in range(num_samples):
        sample = [values[rng.randrange(len(values))] for _ in values]
        sample_means.append(_mean(sample))
    sample_means.sort()
    lower_q = (1.0 - confidence) / 2.0
    upper_q = 1.0 - lower_q
    lower_index = min(max(int(lower_q * (num_samples - 1)), 0), num_samples - 1)
    upper_index = min(max(int(upper_q * (num_samples - 1)), 0), num_samples - 1)
    return sample_means[lower_index], sample_means[upper_index]


def _numeric_values(metric_dicts: list[dict[str, Any]], metric_name: str) -> list[float]:
    values: list[float] = []
    for metrics in metric_dicts:
        value = metrics.get(metric_name)
        if isinstance(value, int | float) and math.isfinite(float(value)):
            values.append(float(value))
    return values


def _is_numeric(value: Any) -> bool:
    return isinstance(value, int | float) and math.isfinite(float(value))


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))
