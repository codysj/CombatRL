# Phase P7 Completion Notes

Phase P7 hardens the Gymnasium wrapper into a stable 2v2 team-aware training
environment. The API remains single-agent: one controlled agent receives RL
actions while the teammate and both opponents use deterministic scripted
policies.

## Implemented

- Canonical 2v2 simulator config with tank and ranged DPS on both teams.
- Controlled-ranged and controlled-tank Gym env configs.
- `scripted_policy_by_agent_id` support for explicit per-agent scripted policy
  assignment.
- Deterministic fallback assignment from teammate and opponent policy fields.
- 2v2 info fields for controlled team, ally/enemy IDs, alive counts, action
  masks, terminal reason, winner, reward breakdown, and event count.
- Ally-aware 49-feature observations with one ally slot and two enemy slots.
- Enemy targetability flags and ally threat indicator tests.
- Team outcome rewards, controlled death penalty, ally death penalty, invalid
  action penalty, and exact reward-breakdown summation tests.
- 2v2 random rollout, replay generation, and PPO smoke compatibility tests.
- `configs/training/ppo_2v2_baseline.yaml`.
- `scripts/run_2v2_env_episode.py` for random, scripted, or checkpoint-driven
  controlled-agent episodes with optional replay capture.
- `scripts/evaluate_2v2_baseline.py` for lightweight deterministic outcome
  summaries.

## Configs

- `configs/env/mvp_2v2_elimination.yaml`
- `configs/env/gym_2v2_controlled_ranged.yaml`
- `configs/env/gym_2v2_controlled_tank.yaml`
- `configs/training/ppo_2v2_baseline.yaml`

Default ranged setup:

- Controlled agent: `team0_ranged_dps_0`
- Teammate: `protector`
- Opponents: `aggressive`, `random`
- Win condition: elimination
- Tick rate: 20 Hz
- Max ticks: 1200
- Decision interval: 4 ticks
- Replay capture: disabled by default

## Observation Notes

The observation remains the fixed 49-feature full-observability layout from P5:
self features, one ally slot, two enemy slots, arena features, and tactical
features. Allies and enemies are sorted live-first, then by increasing distance,
then by `agent_id`. Missing 1v1 slots still encode as stable zero-filled slots
with distance `1.0`.

Recent damage flags remain placeholders set to `0.0`; P7 does not add a memory
or event-history system to observations.

## Rewards

The default reward components are unchanged and inspectable:

- `win_bonus`
- `loss_penalty`
- `damage_dealt`
- `damage_taken_penalty`
- `death_penalty`
- `ally_death_penalty`
- `invalid_action_penalty`
- `time_penalty`

Win/loss rewards use the controlled agent's team outcome. Dense damage reward
and damage-taken penalty only use the controlled agent's own combat by default.

## Running

Check 2v2 random rollouts:

```powershell
uv run python scripts/check_env.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 5 --seed 42
```

Run one 2v2 env episode and save a replay:

```powershell
uv run python scripts/run_2v2_env_episode.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --seed 42 --policy random --save-replay
uv run python scripts/validate_replay.py <replay_path>
uv run python scripts/render_replay.py <replay_path>
```

Run lightweight deterministic baseline evaluation:

```powershell
uv run python scripts/evaluate_2v2_baseline.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 10 --policy random --seed 42
```

Run PPO smoke compatibility:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_2v2_baseline.yaml --smoke
uv run python scripts/evaluate_checkpoint.py <run_dir>/model_final.zip --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 3
```

## Deferred

- Behavior profiles.
- NLP.
- Frontend/backend.
- PettingZoo.
- Self-play and opponent pools.
- Shared team policies.
- Centralized critics.
- RLlib.
- Support/healer role.
- Objective-control mode.
- Advanced metrics framework.
- Skillshots/projectiles and continuous aiming.
- Full simultaneous multi-agent learning.

Recommended next phase: P8 Behavior Profiles.
