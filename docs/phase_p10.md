# Phase P10 Completion Notes

Phase P10 adds natural-language command parsing into validated behavior
profiles.

## Implemented

- `BehaviorProfileParseResult` schema.
- Deterministic rule-based fallback parser.
- Strict parsed-profile validation, repair, base-profile merge, deterministic
  generated profile IDs, and unsupported-request detection.
- Prompt templates for future structured-output LLM use.
- Optional LLM parser interface that accepts an injected callable and requires
  no external service in tests.
- `scripts/parse_command.py` CLI for inspecting and saving parsed profiles.
- `scripts/compare_command_profiles.py` CLI for command-driven profile
  comparisons through the existing P9 benchmark/report stack.
- Parsed profile file support in `PolicySpec.profile_path` for evaluation.
- Unit and integration tests for parse results, fallback rules, validation,
  prompts, parser behavior, saved profiles, and command comparison artifacts.

## Boundary

NLP translates language into `BehaviorProfile` values only. It does not call
`env.step`, output action IDs, mutate simulator state, bypass Pydantic
validation, accept invented behavior-profile fields, execute arbitrary code, or
act as a tactical controller.

## Running

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/parse_command.py "play aggressively"
uv run python scripts/parse_command.py "protect ally"
uv run python scripts/parse_command.py "teleport and buy items"
uv run python scripts/compare_command_profiles.py --commands "play aggressively" "kite backward" --num-seeds 2 --save-replays
uv run python scripts/validate_replay.py <generated_sample_replay_path>
```

## Completion Criteria

- Supported commands produce validated profiles with values in `[0.0, 1.0]`.
- Unsupported mechanics are explicit warnings or errors.
- Unknown LLM fields and out-of-range LLM values fail safely.
- Rule-based parsing is deterministic.
- Parsed profile artifacts load through the existing profile loader.
- Command-driven comparisons write metrics, reports, and optional replay
  samples.

## Deferred

- Frontend/backend dashboard.
- FastAPI routes.
- Live LLM service dependency.
- Raw action generation or direct action control.
- Support/healer behavior.
- Objective-control mode.
- PettingZoo, self-play, opponent pools, and advanced MARL.

Recommended next phase: Phase P11 Backend and Frontend Dashboard.
