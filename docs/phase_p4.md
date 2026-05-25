# Phase P4 Completion Notes

Phase P4 adds deterministic heuristic baseline agents and bot-vs-bot match
support.

## Implemented

- `AgentPolicy` protocol in `combatrl.agents.base`.
- Shared deterministic helper functions in `combatrl.agents.utility`.
- Baseline policies:
  - `RandomBot`
  - `AggressiveBot`
  - `DefensiveBot`
  - `KiterBot`
  - `ProtectorBot`
- Simple policy registry with `create_policy(policy_id, seed)`.
- Lightweight behavior summary for attack attempts, damage, retreat actions,
  final HP, and average nearest-enemy distance.
- `scripts/run_match.py` CLI support for:
  - `--team0-policy`
  - `--team1-policy`
  - `--team0-tank-policy`
  - `--team0-ranged-policy`
  - `--team1-tank-policy`
  - `--team1-ranged-policy`
  - replay saving and frame interval options from P3.
- Bot replay events include `policy_id` in `agent_action_selected` payloads.
- Unit and integration tests for bot behavior, deterministic matches, and replay
  validation.

## Run

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/run_match.py --team0-policy aggressive --team1-policy defensive --seed 42 --save-replay
uv run python scripts/validate_replay.py <printed_replay_path>
uv run python scripts/render_replay.py <printed_replay_path>
```

Additional visual checks:

```powershell
uv run python scripts/run_match.py --team0-policy kiter --team1-policy aggressive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy protector --team1-policy aggressive --seed 42 --save-replay
```

## Completion Criteria

- Every bot returns valid `ActionCommand` values for live agents.
- Dead agents receive `NO_OP`.
- No-live-enemy cases do not crash.
- Same seed plus same policies produces identical final states.
- Same seed plus same policies plus replay produces equivalent replay content,
  ignoring timestamps and output directory.
- Saved bot replays validate with the P3 replay validator.
- Replays visibly show different tactical behavior between baselines.

## Deferred

- Gymnasium wrapper.
- Observation vectors.
- Reward builder.
- PPO/training.
- Behavior profile system.
- NLP.
- Frontend/backend.
- Full evaluation framework and dashboards.
- Support/healer role.
- Objective-control mode.
- PettingZoo/RLlib.

Recommended next phase: P5 Gymnasium Environment Wrapper.
