# Phase P9 Completion Notes

Phase P9 adds a reusable, local evaluation framework for fixed-seed policy and
profile comparisons.

## Implemented

- `PolicySpec`, `ScenarioSpec`, `MatchEvaluationRecord`, and
  `EvaluationResult` schemas.
- Replay/event-based metric computation in `combatrl.evaluation.metrics`.
- Deterministic aggregation utilities with mean/std, simple min/max, and
  outcome rates.
- `BenchmarkSuite` for seeded heuristic, random, profiled, and PPO checkpoint
  evaluation.
- JSON, CSV, JSONL, Markdown, and comparison report writers.
- `scripts/evaluate_policy.py` CLI.
- Starter evaluation suite configs under `configs/evaluation/`.
- `scripts/compare_profiles.py` now routes profile comparisons through the P9
  benchmark/reporting framework.
- Unit and integration tests for schemas, metrics, aggregation, reports,
  benchmark determinism, and CLI smoke execution.

## Metrics

P9 reports outcome, combat, survival, positioning, teamwork, and action/profile
metrics. Optional replay payloads are handled defensively. If a metric cannot be
derived from current replay data, it falls back to a stable default instead of
recomputing simulator behavior.

## Running

Tiny heuristic evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type heuristic --policy-id aggressive --seed-start 100 --num-seeds 3 --save-replays --replay-sample-count 1
```

Tiny profile comparison:

```powershell
uv run python scripts/compare_profiles.py --profiles aggressive defensive protective --base-policy aggressive --num-seeds 3 --save-replays
```

PPO checkpoint evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type ppo_checkpoint --checkpoint <checkpoint_path> --seed-start 1000 --num-seeds 3
```

## Completion Criteria

- Evaluations run across fixed seed lists.
- Per-match metrics are saved as CSV and JSONL.
- Aggregate results are saved as JSON.
- Markdown reports include config metadata, seed summary, metrics, replay sample
  paths, and cautious interpretation notes.
- Replays remain the source for inspection.
- Training, rendering, simulator truth, and evaluation remain separate.

## Deferred

- NLP command parser.
- LLM integration.
- Frontend/backend dashboard.
- Support/healer role.
- Objective-control mode.
- PettingZoo, self-play pools, RLlib, and advanced MARL.
- Database-backed experiment storage.
- Cloud experiment tracking.

Recommended next phase: Phase P10 NLP Command Parser.
