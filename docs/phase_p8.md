# Phase P8 Completion Notes

Phase P8 adds manual behavior profiles for inference-time tactical modulation.

## Implemented

- `BehaviorProfile` schema with bounded numeric axes.
- Profile presets under `configs/profiles/`.
- YAML profile loading, listing, and validation.
- Profile-aware utility scoring and deterministic action reranking.
- `ProfiledBot` composition wrapper for existing heuristic policies.
- Policy registry support for `profiled:<profile>` and
  `profiled:<base_policy>:<profile>`.
- Optional Gymnasium profile fields for scripted agents.
- Profile metrics for damage, survival, spacing, ally distance, action rates,
  and coarse behavior separation.
- `scripts/compare_profiles.py` for fixed-seed profile comparisons with JSON,
  CSV, and optional sample replays.
- Replay action events include `profile_id`, `valid`, and `fallback_used` when
  policy metadata is available. Movement events include `action_type`.
- Unit and integration tests for schema validation, loader failures, modulation
  differences, wrapper determinism, replay determinism, and saved replay
  validation.

## Run

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python -c "from combatrl.profiles.loader import list_profiles; print(list_profiles())"
uv run python scripts/compare_profiles.py --profiles aggressive defensive protective kiter balanced --base-policy aggressive --num-seeds 10 --save-replays
uv run python scripts/validate_replay.py <sample_replay_path>
uv run python scripts/render_replay.py <sample_replay_path>
```

## Completion Criteria

- Invalid profile YAML fails clearly.
- Same scenario, seed, and profile are deterministic.
- Different profiles produce visible and measurable action differences.
- Profile logic never mutates simulator state or bypasses simulator validation.
- Saved profile comparison replays validate.

## Deferred

- NLP command parser and LLM calls.
- Frontend/backend.
- Objective-control profile effects.
- Support/healer role.
- PettingZoo, self-play, and opponent pools.
- Full P9 evaluation framework.
- Policy conditioning or retraining per profile.

Recommended next phase: Phase P9 Evaluation Framework.
