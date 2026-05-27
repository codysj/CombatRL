"""Local JSON, CSV, JSONL, and Markdown evaluation reports."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from combatrl.schemas.evaluation import EvaluationResult, MatchEvaluationRecord


def write_evaluation_json(result: EvaluationResult, output_path: str | Path) -> Path:
    """Write an aggregate evaluation result JSON file."""
    path = _ensure_parent(output_path)
    path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_per_match_csv(records: list[MatchEvaluationRecord], output_path: str | Path) -> Path:
    """Write per-match records to a spreadsheet-friendly CSV file."""
    path = _ensure_parent(output_path)
    metric_names = sorted({metric for record in records for metric in record.metrics})
    base_fields = [
        "evaluation_id",
        "match_id",
        "scenario_id",
        "seed",
        "policy_id",
        "opponent_id",
        "profile_id",
        "replay_path",
        "terminal_reason",
        "winner_team_id",
        "controlled_team_id",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[*base_fields, *metric_names])
        writer.writeheader()
        for record in sorted(records, key=lambda item: (item.seed, item.match_id)):
            row: dict[str, Any] = {field: getattr(record, field) for field in base_fields}
            row.update({metric: record.metrics.get(metric) for metric in metric_names})
            writer.writerow(row)
    return path


def write_per_match_jsonl(records: list[MatchEvaluationRecord], output_path: str | Path) -> Path:
    """Write per-match records as one JSON object per line."""
    path = _ensure_parent(output_path)
    with path.open("w", encoding="utf-8") as file:
        for record in sorted(records, key=lambda item: (item.seed, item.match_id)):
            file.write(json.dumps(record.model_dump(mode="json"), sort_keys=True) + "\n")
    return path


def write_markdown_report(
    result: EvaluationResult,
    records: list[MatchEvaluationRecord],
    output_path: str | Path,
) -> Path:
    """Write a concise human-readable report with cautious interpretation notes."""
    path = _ensure_parent(output_path)
    seeds = sorted(record.seed for record in records)
    seed_summary = _seed_summary(seeds)
    lines = [
        f"# CombatRL Evaluation: {result.evaluation_id}",
        "",
        "## Configuration",
        "",
        f"- `evaluation_id`: `{result.evaluation_id}`",
        f"- `scenario_id`: `{result.scenario_id}`",
        f"- `policy_id`: `{result.policy_id}`",
        f"- `profile_id`: `{result.profile_id}`",
        f"- `opponent_id`: `{result.opponent_id}`",
        f"- `num_matches`: `{result.num_matches}`",
        f"- `seeds`: `{seed_summary}`",
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for metric_name, metric_value in sorted(result.aggregate_metrics.items()):
        lines.append(f"| `{metric_name}` | {_format_metric(metric_value)} |")

    lines.extend(["", "## Replay Samples", ""])
    if result.replay_sample_paths:
        lines.extend(f"- `{replay_path}`" for replay_path in result.replay_sample_paths)
    else:
        lines.append("- No replay samples were saved.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            _interpretation_note(result),
            "Replay files remain the source for post-hoc inspection of individual match behavior.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_comparison_report(
    results: list[EvaluationResult],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Write JSON and Markdown summaries comparing multiple EvaluationResult objects."""
    if not results:
        msg = "cannot write comparison report for empty results"
        raise ValueError(msg)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "comparison_results.json"
    md_path = output_path / "comparison_report.md"
    payload = [result.model_dump(mode="json") for result in sorted(results, key=_result_sort_key)]
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    metric_names = sorted(
        {
            metric_name
            for result in results
            for metric_name in result.aggregate_metrics
            if metric_name.startswith(("win_rate", "mean_", "std_"))
        }
    )
    lines = [
        "# CombatRL Evaluation Comparison",
        "",
        "| Policy | Profile | Opponent | Matches | " + " | ".join(metric_names) + " |",
        "|---|---|---|---:|" + "|".join("---:" for _ in metric_names) + "|",
    ]
    for result in sorted(results, key=_result_sort_key):
        metric_values = [
            _format_metric(result.aggregate_metrics.get(metric_name, 0.0))
            for metric_name in metric_names
        ]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{result.policy_id}`",
                    f"`{result.profile_id}`",
                    f"`{result.opponent_id}`",
                    str(result.num_matches),
                    *metric_values,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Interpretation should stay cautious, especially below 20 matches. "
            "For MVP comparisons, prefer at least 30 seeds and inspect representative replays.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def _ensure_parent(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _seed_summary(seeds: list[int]) -> str:
    if not seeds:
        return "none"
    if seeds == list(range(seeds[0], seeds[-1] + 1)):
        return f"{seeds[0]}..{seeds[-1]}"
    return ", ".join(str(seed) for seed in seeds)


def _format_metric(value: float | int | str | None) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _interpretation_note(result: EvaluationResult) -> str:
    match_note = (
        "This run has fewer than 20 matches, so treat differences as smoke-test signals only."
        if result.num_matches < 20
        else (
            "This run has enough matches for a basic comparison, "
            "but replay inspection is still recommended."
        )
    )
    attack_rate = result.aggregate_metrics.get("mean_attack_action_rate")
    retreat_rate = result.aggregate_metrics.get("mean_retreat_action_rate")
    behavior_note = ""
    if attack_rate is not None and retreat_rate is not None:
        behavior_note = (
            f" Attack and retreat rates were {attack_rate:.3f} and {retreat_rate:.3f} in this run."
        )
    return match_note + behavior_note


def _result_sort_key(result: EvaluationResult) -> tuple[str, str, str]:
    return (result.scenario_id, result.policy_id, result.profile_id or "")
