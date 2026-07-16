# CombatRL Evaluation Framework

Phase P9 adds a local, replay-based evaluation framework for comparing
heuristic policies, profiled policies, random policies, and PPO checkpoints
across fixed seeds.

Evaluation is separate from training. Training metrics describe optimization
progress inside a training run. Evaluation metrics describe behavior and match
outcomes across a seeded scenario suite after a policy is selected.

## Artifacts

Evaluation artifacts are written under:

```text
artifacts/metrics/evaluations/<evaluation_id>/
```

Each run writes:

- `evaluation_result.json`: aggregate `EvaluationResult`.
- `per_match_metrics.csv`: one row per seed.
- `per_match_metrics.jsonl`: one `MatchEvaluationRecord` per line.
- `evaluation_report.md`: human-readable report with cautious interpretation.
- `replays/`: optional saved replay samples.

Replay files remain the source for post-hoc inspection. Evaluation code consumes
frames and events and does not mutate simulator behavior.

## Supported Policy Types

- `heuristic`: uses the existing P4 policy registry.
- `random`: uses the seeded random bot or random valid Gym action selection.
- `profiled`: wraps a base heuristic with a P8 behavior profile.
- `ppo_checkpoint`: loads a Stable-Baselines3 PPO checkpoint and predicts through
  the Gym environment, deterministic by default.

## Metrics

Core per-match metrics include:

- outcome: `win`, `loss`, `draw_or_timeout`
- combat: `damage_dealt`, `damage_taken`, `eliminations`, `deaths`,
  `attack_attempts`, `successful_attacks`, `damage_per_survival_tick`
- survival: `survival_ticks`, `controlled_agent_died`, `final_hp`,
  `final_hp_norm`
- positioning: `avg_distance_to_nearest_enemy`, `avg_distance_to_ally`,
  `time_in_attack_range_rate`, `time_in_enemy_threat_range_rate`,
  `center_control_rate`
- teamwork: `shared_target_rate`, `ally_peel_rate`, `ally_survival_ticks`,
  `cohesion_score`
- behavior/action: `attack_action_rate`, `retreat_action_rate`,
  `low_hp_chase_rate`, `no_op_rate`, `invalid_action_rate`

`shared_target_rate` and `ally_peel_rate` require `target_intent_id` on attack
action events. They return `null` for older replays without that evidence
instead of treating unavailable intent as a measured zero.
`teamwork_intent_evidence_rate` reports the fraction of controlled attack
actions carrying the required evidence.

Aggregates include `mean_<metric>`, `std_<metric>`, simple min/max values for
key numeric metrics, `num_matches`, `win_rate`, `loss_rate`, and `timeout_rate`.

## Running

Heuristic evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type heuristic --policy-id aggressive --opponents defensive defensive --seed-start 100 --num-seeds 30 --save-replays
```

Profile evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type profiled --base-policy aggressive --profile aggressive --seed-start 100 --num-seeds 30 --save-replays
```

Command-profile comparison:

```powershell
uv run python scripts/compare_command_profiles.py --commands "play aggressively" "protect ally" "kite backward" --num-seeds 3 --save-replays
```

Command comparisons parse each command into a validated behavior profile, save
the parsed profile artifacts, run the existing P9 benchmark/report utilities,
and write JSON, CSV, Markdown, and optional replay samples under
`artifacts/metrics/command_profiles/`.

PPO checkpoint evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type ppo_checkpoint --checkpoint artifacts/checkpoints/.../model_final.zip --seed-start 1000 --num-seeds 30
```

Tiny smoke evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type heuristic --policy-id aggressive --seed-start 100 --num-seeds 3 --save-replays --replay-sample-count 1
```

Validate and render a sample replay:

```powershell
uv run python scripts/validate_replay.py <sample_replay_path>
uv run python scripts/render_replay.py <sample_replay_path>
```

## Scenario Suite Configs

Starter human-readable suite configs live under `configs/evaluation/`:

- `mvp_2v2_profiles.yaml`
- `mvp_2v2_heuristics.yaml`
- `ppo_2v2_baseline_eval.yaml`

For Phase P9, script arguments are the canonical execution interface. The YAML
files document recommended suite defaults.

## Interpretation

Do not make strong claims from fewer than 20 matches. MVP comparisons should
prefer at least 30 seeds, inspect representative replays, and report behavior
differences with cautious wording. For example: "Aggressive profile showed
higher `attack_action_rate` than defensive in this run."

Dashboard/frontend views, database experiment storage, W&B/MLflow integration,
PettingZoo, self-play pools, and advanced MARL are deferred.
