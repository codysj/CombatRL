"""Evaluation report writer tests."""

import json

from combatrl.core.constants import METRICS_SCHEMA_VERSION
from combatrl.evaluation.reports import (
    write_evaluation_json,
    write_markdown_report,
    write_per_match_csv,
    write_per_match_jsonl,
)
from combatrl.schemas.evaluation import EvaluationResult, MatchEvaluationRecord


def test_report_files_are_written_with_expected_keys(tmp_path) -> None:
    record = _record()
    result = EvaluationResult(
        metrics_schema_version=METRICS_SCHEMA_VERSION,
        evaluation_id="eval_report_test",
        scenario_id="scenario",
        policy_id="aggressive",
        opponent_id="defensive",
        profile_id=None,
        num_matches=1,
        seed_start=100,
        aggregate_metrics={"win_rate": 1.0, "mean_damage_dealt": 10.0, "num_matches": 1.0},
        per_match_metrics_path=str(tmp_path / "per_match.csv"),
        replay_sample_paths=["sample_replay"],
    )

    json_path = write_evaluation_json(result, tmp_path / "evaluation_result.json")
    csv_path = write_per_match_csv([record], tmp_path / "per_match.csv")
    jsonl_path = write_per_match_jsonl([record], tmp_path / "per_match.jsonl")
    md_path = write_markdown_report(result, [record], tmp_path / "evaluation_report.md")

    assert json.loads(json_path.read_text(encoding="utf-8"))["evaluation_id"] == "eval_report_test"
    assert "damage_dealt" in csv_path.read_text(encoding="utf-8")
    assert "match_id" in jsonl_path.read_text(encoding="utf-8")
    markdown = md_path.read_text(encoding="utf-8")
    assert "Aggregate Metrics" in markdown
    assert "eval_report_test" in markdown


def _record() -> MatchEvaluationRecord:
    return MatchEvaluationRecord(
        evaluation_id="eval_report_test",
        match_id="match",
        scenario_id="scenario",
        seed=100,
        policy_id="aggressive",
        opponent_id="defensive",
        profile_id=None,
        replay_path="sample_replay",
        terminal_reason="elimination",
        winner_team_id=0,
        controlled_team_id=0,
        metrics={"win": 1, "loss": 0, "draw_or_timeout": 0, "damage_dealt": 10.0},
    )
