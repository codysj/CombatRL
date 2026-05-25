# Phase P6 Completion Notes

Phase P6 adds the first Stable-Baselines3 PPO baseline for the existing
Gymnasium wrapper.

## Implemented

- SB3 PPO dependency and TensorBoard logging dependency.
- Default 1v1 ranged-vs-random Gym env config.
- PPO training config: `configs/training/ppo_1v1_baseline.yaml`.
- `PPOTrainingConfig` schema and YAML loader.
- `DummyVecEnv` factory with unique per-env seeds.
- Headless `train_ppo` module and CLI.
- SB3 EvalCallback and CheckpointCallback setup.
- Final checkpoint saving to `model_final.zip`.
- Local checkpoint metadata JSON.
- Headless checkpoint evaluation module and CLI.
- Optional sample replay generation from an evaluated checkpoint.
- Focused config, registry, vector-env, PPO smoke, and evaluation tests.

## Dependency Note

The canonical spec lists Gymnasium `1.3.0` and SB3 `2.8.0`, but SB3 `2.8.0`
declares `gymnasium<1.3.0`. The project dependency is therefore relaxed to
`gymnasium>=1.2,<1.3` so the required stable SB3 PPO baseline can resolve
without prerelease packages.

## Artifact Contract

Training writes timestamped runs under:

```text
artifacts/checkpoints/ppo_1v1_baseline/run_<timestamp>/
```

Expected files:

- `model_final.zip`
- `best_model.zip` when an SB3 evaluation callback fires and improves
- `config.yaml`
- `metrics.json`
- `evaluation_metrics.json`
- `model_metadata.json`
- `eval_history.csv` when callback evaluation history exists
- `sample_replays/` when replay capture is requested

Checkpoint metadata includes policy ID, algorithm, checkpoint path, env config
path, training config path, observation/action schema versions, timesteps, seed,
SB3 version, CombatRL version, and creation time.

## Commands

Smoke train:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml --smoke
```

Longer train:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml
```

Evaluate:

```powershell
uv run python scripts/evaluate_checkpoint.py <run_dir>/model_final.zip --env-config configs/env/gym_1v1_ranged_vs_random.yaml --episodes 5 --seed-start 1000
```

Generate and validate sample replay:

```powershell
uv run python scripts/evaluate_checkpoint.py <checkpoint> --env-config configs/env/gym_1v1_ranged_vs_random.yaml --episodes 1 --save-replay
uv run python scripts/validate_replay.py <sample_replay_path>
```

## Metrics

Evaluation reports:

- `mean_reward`
- `std_reward`
- `win_rate`
- `loss_rate`
- `timeout_rate`
- `mean_episode_length`
- `invalid_action_rate`
- `mean_damage_dealt`
- `mean_damage_taken`

## Deferred

- Behavior profiles.
- NLP.
- Frontend/backend.
- PettingZoo.
- Self-play and opponent pools.
- Advanced MARL.
- Custom PyTorch policy architectures.
- RLlib.
- W&B/MLflow.
- Objective-control mode.
- Support/healer role.
- Live rendering during training.
- Large-scale training infrastructure.

The smoke test does not assert learning quality. The required "beats random"
criterion remains a longer manual verification target.

Recommended next phase: P7 2v2 Team Environment.
