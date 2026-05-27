# CombatRL Gymnasium Environment

`CombatRLGymEnv` is a single-agent Gymnasium wrapper around the deterministic
simulator. In the default P7 setup, one controlled agent acts alongside one
scripted teammate against two scripted opponents. Gymnasium does not own game
rules: movement, combat,
cooldowns, deaths, terminal state, events, and invariants remain in
`SimulationEngine`.

## Default Setup

Default config: `configs/env/gym_2v2_controlled_ranged.yaml`

- Controlled agent: `team0_ranged_dps_0`
- Teammate policy: `protector`
- Opponent policies: `aggressive`, `random`
- Simulation config: `configs/env/mvp_2v2_elimination.yaml`
- `render_mode=None` by default
- Replay capture disabled by default

Optional explicit policy assignment:

```yaml
scripted_policy_by_agent_id:
  team0_tank_0: protector
  team1_tank_0: aggressive
  team1_ranged_dps_0: random
```

When this mapping is present, every non-controlled agent must be assigned a
known scripted policy and the controlled agent must be omitted.

Optional profile assignment:

```yaml
teammate_profile_id: protective
opponent_profile_ids:
  - aggressive
  - kiter
profile_by_agent_id:
  team0_tank_0: protective
controlled_profile_id: defensive
rerank_controlled_action_with_profile: false
```

Scripted teammate and opponent policies can be wrapped with profiles. The
controlled RL action is not reranked unless
`rerank_controlled_action_with_profile` is explicitly enabled. P8 does not
change observation shape or train behavior-conditioned policies.

## API Contract

```python
from combatrl.envs import CombatRLGymEnv

env = CombatRLGymEnv("configs/env/gym_2v2_controlled_ranged.yaml")
observation, info = env.reset(seed=42)
observation, reward, terminated, truncated, info = env.step(0)
env.close()
```

Spaces:

- `observation_space = Box(low=-1.0, high=1.0, shape=(49,), dtype=np.float32)`
- `action_space = Discrete(10)`

Termination and truncation:

- Elimination win/loss: `terminated=True`, `truncated=False`
- Max ticks: `terminated=False`, `truncated=True`
- Invariant failure: `terminated=False`, `truncated=True`, with `info["error"]`

Step `info` includes match identity, controlled team, ally/enemy IDs, alive
counts, terminal reason, winner, reward breakdown, invalid-action flag, next
action mask, and event count.

## Action Space

| ID | Action |
|---:|---|
| 0 | `NO_OP` |
| 1 | `MOVE_UP` |
| 2 | `MOVE_DOWN` |
| 3 | `MOVE_LEFT` |
| 4 | `MOVE_RIGHT` |
| 5 | `MOVE_UP_LEFT` |
| 6 | `MOVE_UP_RIGHT` |
| 7 | `MOVE_DOWN_LEFT` |
| 8 | `MOVE_DOWN_RIGHT` |
| 9 | `ATTACK_NEAREST` |

Invalid action IDs and mask-invalid actions fall back to `NO_OP`, set
`info["invalid_action"] = True`, and receive the invalid-action reward penalty.

## Observation Layout

The observation vector has 49 named features:

- Self, 10: HP, normalized position and velocity, cooldowns, role one-hot.
- Ally slot, 9: alive flag, relative position, distance, HP, role, threat flag.
- Enemy slot 1, 9: alive flag, relative position, distance, HP, role, in-range flag.
- Enemy slot 2, 9: same layout as enemy slot 1.
- Arena, 6: wall distances and relative center vector.
- Tactical, 6: nearest enemy/ally distances, outnumbered flag, recent damage
  placeholders, attack-ready flag.

Entity ordering is deterministic: live entities before dead entities, then
increasing distance from the controlled agent, then `agent_id`. Missing slots are
filled with zero flags, zero relative position, distance `1.0`, and zero role
values. Recent damage flags are placeholders set to `0.0` in P7.

## Reward Components

Every `RewardBreakdown` includes these components:

- `win_bonus`: `+1.0` on controlled-team elimination win
- `loss_penalty`: `-1.0` on controlled-team elimination loss
- `damage_dealt`: controlled damage to enemies divided by `100.0`
- `damage_taken_penalty`: controlled damage received divided by `-150.0`
- `death_penalty`: `-0.5` if the controlled agent dies this step
- `ally_death_penalty`: `-0.25` per controlled ally death this step
- `invalid_action_penalty`: `-0.02` for one invalid RL action
- `time_penalty`: `-0.001` per env step

`reward_config` scales component values multiplicatively and may be partial.

## 2v2 Replay And Evaluation

Run one 2v2 episode through the Gym env and save a replay:

```powershell
uv run python scripts/run_2v2_env_episode.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --seed 42 --policy random --save-replay
```

Run a lightweight 2v2 baseline summary:

```powershell
uv run python scripts/evaluate_2v2_baseline.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 10 --seed 42
```

## Limitations

P8 includes lightweight behavior profiles for scripted policies. It does not
include NLP, frontend/backend, PettingZoo, self-play, opponent pools, shared
team policies, centralized critics, support/healer mechanics, objective-control
mode, full evaluation framework metrics, or simultaneous multi-agent learning.

## Manual Verification

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/check_env.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 3 --seed 42
uv run python scripts/run_2v2_env_episode.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --seed 42 --policy random --save-replay
```

Determinism check:

```powershell
uv run python scripts/check_env.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 2 --seed 42
uv run python scripts/check_env.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 2 --seed 42
```

The summaries should match for fixed seeds.
