# CombatRL Behavior Profiles

Behavior profiles are manual, bounded numeric control objects that modulate
agent decisions at inference time. They come before NLP so behavior control can
be tested independently from language parsing.

Profiles do not retrain policies, change observations, mutate simulator state,
or override simulator rules. They only rerank valid MVP `ActionCommand`
candidates before the simulator applies actions.

## Schema

Profiles use `profile_schema_version: "1.0"` and these axes, each in
`[0.0, 1.0]`:

- `aggression`: favors closing distance, attacks, and weak enemy targets.
- `caution`: favors retreating under pressure and avoiding close threats.
- `cohesion`: favors staying near allies and avoiding overextension.
- `protectiveness`: favors moving toward threatened allies and peeling threats.
- `focus_fire`: favors attacking an ally's current target when known.
- `greed`: favors chasing low-HP enemies.
- `spacing`: favors maintaining range, especially for ranged DPS agents.
- `objective_bias`: reserved for future objective-control mode.

Preset YAML files live in `configs/profiles/`:

- `balanced`
- `aggressive`
- `defensive`
- `kiter`
- `protective`

Load them with:

```powershell
uv run python -c "from combatrl.profiles.loader import list_profiles; print(list_profiles())"
```

## Agent Usage

Policy IDs support:

```text
profiled:<profile>
profiled:<base_policy>:<profile>
```

Examples:

```powershell
uv run python scripts/run_match.py --team0-policy profiled:aggressive --team1-policy defensive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy aggressive --team0-profile protective --team1-policy aggressive --seed 42 --save-replay
```

The `ProfiledBot` wrapper calls its base policy, builds the small MVP candidate
set (`NO_OP`, movement actions, and `ATTACK_NEAREST` when enemies exist), gives
the base action a small advantage, then applies profile utility scoring. Ties
resolve by stable action ordering.

## Gymnasium Support

`EnvironmentConfig` supports optional profile fields for scripted agents:

- `teammate_profile_id`
- `opponent_profile_ids`
- `profile_by_agent_id`
- `controlled_profile_id`
- `rerank_controlled_action_with_profile`

Controlled RL actions are not reranked by default, and P8 does not change
observation shape or train behavior-conditioned policies.

## Comparison Metrics

Run:

```powershell
uv run python scripts/compare_profiles.py --profiles aggressive defensive protective kiter balanced --base-policy aggressive --num-seeds 10 --save-replays
```

The script now uses the Phase P9 evaluation framework. It writes per-profile
evaluation folders, JSON and CSV summary metrics, a Markdown comparison report,
and one sample replay per profile when requested. The table includes damage,
survival, ally distance, enemy distance, attack rate, retreat rate, and win
rate. Expected coarse differences:

- aggressive profiles attack more often than defensive profiles.
- defensive profiles retreat more often under close pressure.
- protective profiles stay closer to allies than aggressive profiles.
- kiter profiles maintain more distance from nearby enemies.

Validate and render sample replays with:

```powershell
uv run python scripts/validate_replay.py <sample_replay_path>
uv run python scripts/render_replay.py <sample_replay_path>
```

## Limitations

P8 keeps behavior modulation inspectable and lightweight. It does not add NLP,
LLM calls, frontend/backend, objective control, support/healer behavior,
PettingZoo, self-play, opponent pools, or learned behavior-conditioned policies.
P9 adds fixed-seed local evaluation, but profile metrics are still replay/event
derived and some teamwork metrics remain best-effort until richer target intent
payloads exist.

Recommended next phase: Phase P10 NLP Command Parser.
