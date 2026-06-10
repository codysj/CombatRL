# CombatRL RL Training

CombatRL training is headless and layered above the Gymnasium wrapper:

```text
training -> env wrappers -> simulator public API
```

The simulator does not import training code, and training does not require the
renderer, Pygame, browser, FastAPI, frontend code, experiment trackers, or a
database.

## PPO Baseline

The first baseline is Stable-Baselines3 PPO using `MlpPolicy`. PPO is used first
because it is a standard on-policy baseline, integrates directly with
Gymnasium, supports simple vectorized CPU rollouts, and saves portable `.zip`
checkpoints.

Default config:

```text
configs/training/ppo_1v1_baseline.yaml
```

2v2 P7 config:

```text
configs/training/ppo_2v2_baseline.yaml
```

Key fields:

- `env_config_path`: Gym env config used for training and evaluation.
- `total_timesteps`: non-smoke training budget.
- `smoke_total_timesteps`: tiny CI/local smoke budget.
- `n_envs`: number of `DummyVecEnv` envs.
- `n_steps`, `batch_size`, `n_epochs`: PPO rollout/update sizes.
- `eval_freq`, `eval_episodes`: SB3 evaluation callback cadence.
- `checkpoint_freq`: periodic checkpoint cadence.
- `output_dir`: root directory for timestamped run outputs.
- `save_sample_replay`: whether final evaluation writes one replay.

Every vectorized env receives `seed + rank`. Evaluation envs are separate and
use a seed offset.

## Running

Install/sync:

```powershell
uv sync
```

Smoke train:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml --smoke
uv run python scripts/train_ppo.py --config configs/training/ppo_2v2_baseline.yaml --smoke
```

Longer train:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml
```

Override timesteps or seed:

```powershell
uv run python scripts/train_ppo.py --smoke --total-timesteps 2048 --seed 7
```

## Curriculum Training (PPO Trainability Pass)

The flat 2v2 task is too sparse for PPO from scratch: spawns are ~70 units
apart with attack range 18, so exploration never finds combat and passivity is
a stable local optimum. The supported recipe is a staged curriculum with light
opt-in reward shaping, warm-starting each stage from the previous checkpoint:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_curriculum_s1_close1v1.yaml
uv run python scripts/train_ppo.py --config configs/training/ppo_curriculum_s2_1v1_random.yaml --init-checkpoint <s1_run_dir>/model_final.zip
uv run python scripts/train_ppo.py --config configs/training/ppo_curriculum_s3_1v1_aggressive.yaml --init-checkpoint <s2_run_dir>/model_final.zip
uv run python scripts/train_ppo.py --config configs/training/ppo_curriculum_s4_close2v2.yaml --init-checkpoint <s3_run_dir>/model_final.zip
uv run python scripts/train_ppo.py --config configs/training/ppo_curriculum_s5_2v2.yaml --init-checkpoint <s4_run_dir>/model_final.zip
```

Stages: close 1v1 vs random → full 1v1 vs random → 1v1 vs aggressive → close
2v2 → canonical 2v2. The `*_shaped` env configs enable four reward components
that default to weight 0.0 everywhere else: `approach_reward`,
`attack_range_bonus`, `attack_landed_bonus`, and `edge_penalty`. Final
evaluation always uses the canonical unshaped scenario
(`configs/env/gym_2v2_controlled_ranged.yaml`).

Gate each stage on its `evaluation_metrics.json` before continuing: expect
nonzero `mean_damage_dealt`, low `timeout_rate`, and a sane `action_histogram`
(the histogram makes degenerate policies such as 100% `MOVE_UP` or no-op spam
obvious). Replay-derived P9 metrics additionally report per-action
`action_rate_*` and `edge_occupancy_rate`.

Results of the 2026-06-10 trainability pass (96.7% win rate over seeds
1000–1029 on the canonical 2v2 scenario versus 0% for random) are documented
in `artifacts/reports/ppo_trainability_pass_20260610.md`.

## Evaluating

```powershell
uv run python scripts/evaluate_checkpoint.py <run_dir>/model_final.zip --env-config configs/env/gym_1v1_ranged_vs_random.yaml --episodes 5 --seed-start 1000
uv run python scripts/evaluate_checkpoint.py <run_dir>/model_final.zip --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 3 --seed-start 1000
```

Add `--save-replay` to write one evaluated-policy replay under
`artifacts/replays` unless a training run provides a run-local replay output
directory.

Phase P9 also supports PPO checkpoint evaluation through the shared fixed-seed
evaluation framework:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type ppo_checkpoint --checkpoint <run_dir>/model_final.zip --seed-start 1000 --num-seeds 30
```

`evaluate_policy.py` writes aggregate JSON, per-match CSV/JSONL, Markdown, and
optional replay samples under `artifacts/metrics/evaluations/`. PPO prediction
is deterministic by default; pass `--stochastic` only for deliberate stochastic
policy inspection.

## Manual Verification

Run:

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml --smoke
uv run python scripts/train_ppo.py --config configs/training/ppo_2v2_baseline.yaml --smoke
uv run python scripts/evaluate_checkpoint.py <smoke_run_dir>/model_final.zip --env-config configs/env/gym_1v1_ranged_vs_random.yaml --episodes 2
```

Confirm finite `mean_reward`, `win_rate`, `timeout_rate`, and
`mean_episode_length`. For real learning claims, increase timesteps gradually
from 25k to 100k to 250k, compare against random, and inspect sample replays.
Use the P9 evaluation script with at least 30 seeds before making policy-quality
claims.
