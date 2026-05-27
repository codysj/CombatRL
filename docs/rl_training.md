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
