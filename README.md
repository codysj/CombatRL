# CombatRL

CombatRL is a deterministic, headless-first tactical arena simulation project for
studying reinforcement learning, multi-agent behavior, replay analytics, and
behavior-profile control. The simulator is intentionally built around stable
schemas and replay-first debugging so later systems can be tested independently.

## Phase Status

Phase P1 establishes the smallest deterministic headless simulator state layer.
The project can load the default MVP config, initialize a 2v2 match state,
advance ticks without movement or combat, validate invariants, and terminate by
timeout at `max_ticks`.

Simulator combat, movement intents, damage, death resolution, replay writing,
rendering, RL training, heuristic agents, behavior profiles, frontend, backend,
and NLP systems are intentionally not implemented yet.

## Setup

Install dependencies:

```powershell
uv sync --extra dev
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

Expected summary fields include:

- `scenario_id: mvp_2v2_elimination`
- `agent_count: 4`
- `final_tick: 1200`
- `terminal: true`
- `terminal_reason: timeout`
- `winner_team_id: None`

## Manual Verification

Run:

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/run_match.py --seed 42
```

Run the script twice with the same seed and confirm the summary output is
identical. To check validation manually, temporarily move a spawn position
outside the arena in `configs/env/mvp_2v2_elimination.yaml`, confirm loading or
invariant validation fails, then revert the edit.

Next phase: P2 Movement, Combat, and Win Conditions.
