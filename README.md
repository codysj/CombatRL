# CombatRL

CombatRL is a deterministic, headless-first tactical arena simulation project for
studying reinforcement learning, multi-agent behavior, replay analytics, and
behavior-profile control. The simulator is intentionally built around stable
schemas and replay-first debugging so later systems can be tested independently.

## Phase 0 Status

Phase P0 establishes the repository, package, configuration schema, deterministic
RNG wrapper, geometry helpers, and foundational tests. Simulator combat,
movement, replay, RL training, rendering, frontend, backend, and NLP systems are
intentionally not implemented yet.

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
