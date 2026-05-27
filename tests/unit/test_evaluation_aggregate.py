"""Evaluation aggregation tests."""

import pytest

from combatrl.evaluation.aggregate import aggregate_match_records, aggregate_metric_dicts
from combatrl.schemas.evaluation import MatchEvaluationRecord


def test_win_rate_from_records_is_correct_and_order_independent() -> None:
    records = [
        _record(seed=2, match_id="b", win=0, loss=1, timeout=0, damage=4.0),
        _record(seed=1, match_id="a", win=1, loss=0, timeout=0, damage=10.0),
        _record(seed=3, match_id="c", win=0, loss=0, timeout=1, damage=2.0),
    ]

    aggregate = aggregate_match_records(records)
    reverse_aggregate = aggregate_match_records(list(reversed(records)))

    assert aggregate["win_rate"] == pytest.approx(1.0 / 3.0)
    assert aggregate["loss_rate"] == pytest.approx(1.0 / 3.0)
    assert aggregate["timeout_rate"] == pytest.approx(1.0 / 3.0)
    assert aggregate == reverse_aggregate


def test_mean_std_metrics_are_correct() -> None:
    aggregate = aggregate_metric_dicts(
        [
            {"win": 1, "loss": 0, "draw_or_timeout": 0, "damage_dealt": 10.0},
            {"win": 0, "loss": 1, "draw_or_timeout": 0, "damage_dealt": 4.0},
        ]
    )

    assert aggregate["mean_damage_dealt"] == 7.0
    assert aggregate["std_damage_dealt"] == 3.0
    assert aggregate["min_damage_dealt"] == 4.0
    assert aggregate["max_damage_dealt"] == 10.0


def test_empty_input_fails_clearly() -> None:
    with pytest.raises(ValueError, match="empty"):
        aggregate_metric_dicts([])


def _record(
    *,
    seed: int,
    match_id: str,
    win: int,
    loss: int,
    timeout: int,
    damage: float,
) -> MatchEvaluationRecord:
    return MatchEvaluationRecord(
        evaluation_id="eval",
        match_id=match_id,
        scenario_id="scenario",
        seed=seed,
        policy_id="policy",
        opponent_id="opponent",
        profile_id=None,
        replay_path=None,
        terminal_reason=None,
        winner_team_id=None,
        controlled_team_id=0,
        metrics={
            "win": win,
            "loss": loss,
            "draw_or_timeout": timeout,
            "damage_dealt": damage,
        },
    )
