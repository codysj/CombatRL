# Generalization Evaluation

CRL-003 adds deterministic team-level spawn translation through
`spawn_randomization` in environment configs. Each team formation is preserved,
offsets are bounded by both configuration and arena dimensions, and the episode
seed fully determines the result. The underlying simulation config is not
mutated.

Committed scenarios:

- `configs/env/gym_2v2_generalization_ranged.yaml`
- `configs/env/gym_2v2_generalization_tank.yaml`

The baseline gate for any policy claim is 30 fixed seeds per controlled role and
opponent set, at least three saved replay samples, and explicit reporting of
win/loss/timeout, survival, damage, action rates, and failure modes. Mixed
opponents must contain at least two policy types. A result on one role must not
be generalized to the other role.

Example:

```powershell
uv run python scripts/evaluate_policy.py `
  --scenario configs/env/gym_2v2_generalization_ranged.yaml `
  --policy-type ppo_checkpoint `
  --policy-id ppo_s5 `
  --checkpoint artifacts/checkpoints/ppo_curriculum_s5_2v2/run_20260610T220831Z/model_final.zip `
  --opponents aggressive random `
  --seed-start 1000 `
  --num-seeds 30 `
  --replay-sample-count 3
```

The ranged checkpoint can be evaluated immediately. A tank-controlled policy
still requires training before a learned-policy comparison can satisfy the full
CRL-003 claim.

## 2026-07-16 Baseline Evidence

- Ranged S5 checkpoint, seeds 1000-1029, randomized spawns, mixed aggressive
  and random opponents: 26 wins, 0 losses, 4 timeouts; mean controlled damage
  237.33.
- Tank-controlled aggressive heuristic on the same seeds and distribution:
  30 wins, 0 losses, 0 timeouts; mean controlled damage 5.87.

The tank result is a plumbing baseline and likely reflects teammate contribution;
it is not evidence of tank policy learning. Three replay samples per run were
saved under `artifacts/metrics/evaluations/crl003`.
