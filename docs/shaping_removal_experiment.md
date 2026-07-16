# Reward-Shaping Removal Experiment

CRL-004 uses sequential warm starts from the final S5 checkpoint:

1. `ppo_s5_shaping_half.yaml`
2. `ppo_s5_shaping_quarter.yaml`
3. `ppo_s5_sparse_finetune.yaml`

Each stage keeps simulator mechanics and canonical reward components unchanged;
only the four optional shaping weights are reduced. Run each stage with at least
three training seeds and pass the prior stage checkpoint with
`--init-checkpoint`.

```powershell
uv run python scripts/train_ppo.py `
  --config configs/training/ppo_s5_shaping_half.yaml `
  --init-checkpoint <s5-checkpoint>
```

Evaluate shaped, half, quarter, and sparse checkpoints on the same 30 seeds and
generalization scenario. Compare win rate, damage, survival, invalid/no-op and
per-action rates. Inspect at least three matched-seed replays per checkpoint.

The experiment is complete only after the run directories, comparison table,
and replay findings are recorded. Smoke runs validate wiring but are not
behavioral evidence.

## 2026-07-16 Workflow Verification

The complete warm-start chain passed 1,024-timestep smoke runs:

- half shaping: `artifacts/checkpoints/ppo_s5_shaping_half/run_20260716T192530Z`
- quarter shaping: `artifacts/checkpoints/ppo_s5_shaping_quarter/run_20260716T192613Z`
- sparse fine-tune: `artifacts/checkpoints/ppo_s5_sparse_finetune/run_20260716T192651Z`

These artifacts verify config loading, checkpoint compatibility, training,
evaluation, metadata, and sample replay output. They are intentionally excluded
from behavioral conclusions because the smoke budget is too small.
