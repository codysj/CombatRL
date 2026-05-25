# CombatRL

CombatRL is a deterministic, headless-first tactical arena simulation project for
studying reinforcement learning, multi-agent behavior, replay analytics, and
behavior-profile control. The simulator is intentionally built around stable
schemas and replay-first debugging so later systems can be tested independently.

## Phase Status

Phase P3 adds replay writing, replay reading, replay validation, and a local
optional Pygame debug renderer. The project can load the default MVP config,
initialize a 2v2 match, run scripted discrete actions to elimination or timeout,
save replay artifacts, validate them, and render saved frames without
recomputing simulation logic.

RL training, formal heuristic agents, reward shaping, behavior profiles,
objective control, pathfinding, frontend, backend, and NLP systems are
intentionally not implemented yet.

## Simulator Model

Actions are discrete `ActionCommand` values:

- `NO_OP`
- cardinal and diagonal movement actions
- `ATTACK_NEAREST`

Movement uses fixed timestep logic:

```text
new_position = old_position + normalized_direction * movement_speed * dt
dt = 1.0 / tick_rate_hz
```

Diagonal movement is normalized, positions clamp to the arena, and dead agents
cannot move or attack. Combat is intentionally minimal: `ATTACK_NEAREST` selects
the nearest alive enemy in range, resolves ties by sorted `agent_id`, applies
instant damage, clamps HP at zero, and sets attack cooldown on successful hits.

Per tick, the simulator executes:

1. Validate actions.
2. Resolve movement.
3. Resolve attacks.
4. Apply deaths.
5. Decrement cooldowns.
6. Evaluate terminal state.
7. Increment tick.
8. Validate invariants.

## Setup

Install dependencies:

```powershell
uv sync --extra dev
```

Install the optional renderer:

```powershell
uv sync --extra dev --extra renderer
```

Run tests:

```powershell
uv run pytest
```

Run linting:

```powershell
uv run ruff check .
uv run ruff format --check .
```

Run the headless match script:

```powershell
uv run python scripts/run_match.py --seed 42
```

Run and save a replay:

```powershell
uv run python scripts/run_match.py --seed 42 --save-replay
```

Expected summary fields include:

- `scenario_id: mvp_2v2_elimination`
- `agent_count: 4`
- `final_tick`
- `terminal: true`
- `terminal_reason: elimination` or `terminal_reason: timeout`
- `winner_team_id`
- `replay_path` when `--save-replay` is used
- `replay_frame_count` when `--save-replay` is used
- `replay_event_count` when `--save-replay` is used

## Replays

Replay files are written under:

```text
artifacts/replays/<timestamp>_<scenario_id>_seed-<seed>/
```

Each replay contains:

- `metadata.json`
- `frames.jsonl`
- `events.jsonl`
- `summary.json`

Validate a replay:

```powershell
uv run python scripts/validate_replay.py artifacts/replays/<replay-dir>
```

Render a replay:

```powershell
uv run python scripts/render_replay.py artifacts/replays/<replay-dir>
```

Renderer controls:

- `Space`: pause/play
- `Right arrow`: step forward while paused
- `Left arrow`: step backward while paused
- `1`, `2`, `4`: speed controls
- `Esc` or window close: quit

See `docs/replay_schema.md` and `docs/phase_p3.md` for schema details and
completion notes.

## Manual Verification

Run:

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/run_match.py --seed 42
uv run python scripts/run_match.py --seed 42 --save-replay
```

Run the script twice with the same seed and confirm the summary output is
identical. Validate the printed replay path, render it locally, and confirm the
arena, agents, HP bars, event feed, target lines, pause/play, and frame stepping
work. To check validation manually, temporarily corrupt a replay frame tick or
remove `metadata.json`, confirm `scripts/validate_replay.py` fails clearly, then
revert the corruption.

Next phase: P4 Heuristic Baseline Agents.
