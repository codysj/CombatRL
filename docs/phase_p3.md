# Phase P3 Completion Notes

Phase P3 adds file-based replay capture, replay validation, and a local optional
Pygame debug renderer.

## Implemented

- Versioned replay schemas in `combatrl.schemas.replay`.
- Deterministic simulator event emission for movement, actions, attacks,
  damage, cooldowns, eliminations, match start, and match end.
- Snapshot helpers for scoreboard, replay frames, and replay summaries.
- Replay writer, reader, and validator.
- Replay-enabled `scripts/run_match.py`.
- `scripts/validate_replay.py`.
- `scripts/render_replay.py`.
- Optional `renderer` dependency extra using `pygame-ce`.
- Pygame renderer that reads replay files only.
- Unit and integration tests for schemas, writer/reader, validator,
  roundtrips, determinism, and renderer smoke.

## Run

```powershell
uv sync --extra dev --extra renderer
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/run_match.py --seed 42 --save-replay
uv run python scripts/validate_replay.py <printed_replay_path>
uv run python scripts/render_replay.py <printed_replay_path>
```

## Completion Criteria

- A deterministic scripted match can be saved to replay files.
- Replay files validate after writing.
- Replay reader can reload metadata, frames, events, and summary.
- Same seed and scripted policy produce equivalent frames, events, and summary.
- Renderer can draw the arena, agents, HP bars, attack ranges, target lines,
  velocity vectors when enabled, an event feed, and tick/time overlays.
- Renderer imports and tests do not require Pygame unless the renderer extra is
  installed.

## Deferred

- Heuristic baseline agents.
- Gymnasium wrapper.
- Reward builder.
- PPO/training.
- Behavior profiles.
- NLP.
- Frontend/backend.
- Evaluation framework beyond replay summary.
- Advanced metrics.
- Support/healer mechanics.
- Objective-control mode.
- Projectile/ability systems.

Recommended next phase: P4 Heuristic Baseline Agents.
