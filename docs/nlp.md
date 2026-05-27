# CombatRL NLP Command Parser

Phase P10 adds deterministic natural-language-to-profile parsing. The NLP layer
is a translator only:

```text
natural language -> NLP parser -> profile candidate -> Pydantic validation
-> bounded BehaviorProfile -> behavior modulation / policy conditioning
```

It never selects raw actions, emits action IDs, calls `env.step`, mutates
simulator state, executes code, or invents unsupported mechanics.

## Parse Result

`BehaviorProfileParseResult` contains `success`, `command`, `profile`,
`errors`, `unsupported_requests`, `parser_source`, `raw_output`, and `notes`.
Successful results always include a validated `BehaviorProfile`. Failed results
always include errors or unsupported requests. The original command text is
preserved exactly.

## Rule-Based Parser

The deterministic fallback parser starts from a base profile, usually
`balanced`, and applies bounded axis adjustments:

- aggressive, attack, push, dive, engage: increase aggression, reduce caution.
- defensive, safe, survive, stay alive, avoid dying: increase caution, reduce
  aggression and greed.
- protect, peel, guard, defend ally, protect teammate: increase protectiveness
  and cohesion.
- kite, keep distance, back up, avoid close combat: increase spacing and
  caution.
- focus, focus fire, same target: increase focus fire.
- chase, finish, secure kill, low health enemy: increase greed and aggression.
- group, stay together, stay near ally: increase cohesion.
- balanced, default, normal: return near the balanced profile.

Rule output is trusted internal logic and is clamped to `[0.0, 1.0]`. Manual
YAML profiles and LLM output still go through strict Pydantic validation.

## Unsupported Requests

Unsupported mechanics are surfaced explicitly in `unsupported_requests`.
Current examples include teleporting, items/shop, minions, fog, wards, tower
dive, ultimates, healing/support role behavior, revive, summon, build, and
spells outside the current action system.

Commands with both supported and unsupported intents succeed when a valid
profile is produced, with unsupported requests reported as warnings. Commands
with only unsupported or unknown intents fail instead of silently returning a
fake behavior.

## Optional LLM Interface

`parse_command_to_profile(..., use_llm=True, llm_client=callable)` builds a
structured prompt and passes it to the provided callable. Tests use fake
callables only. There is no network dependency and no required API key.

LLM JSON is untrusted until validated. Unknown fields fail, out-of-range values
fail, and missing axes are filled from the base profile. If `use_llm=True` is
requested without a client, parsing falls back to deterministic rules with
`parser_source="fallback"`.

## CLI

Parse a command:

```powershell
uv run python scripts/parse_command.py "play aggressively"
uv run python scripts/parse_command.py "protect ally and stay together"
uv run python scripts/parse_command.py "kite backward and avoid close combat"
```

Save a parsed profile:

```powershell
uv run python scripts/parse_command.py "protect ally" --output-profile artifacts/profiles/protect_ally.yaml
```

Unsupported requests do not crash:

```powershell
uv run python scripts/parse_command.py "teleport behind them and buy items"
```

## Command Comparisons

Run command-generated profiles through the existing P9 evaluation stack:

```powershell
uv run python scripts/compare_command_profiles.py --commands "play aggressively" "protect ally" "kite backward" --num-seeds 3 --save-replays
```

The script writes parsed profile YAML/JSON artifacts, per-command evaluation
artifacts, a command summary JSON/CSV, comparison reports, and optional sample
replays. Validate and render sample replays with:

```powershell
uv run python scripts/validate_replay.py <sample_replay_path>
uv run python scripts/render_replay.py <sample_replay_path>
```

## Limitations

P10 does not add frontend/backend routes, a live LLM service, raw action
generation, simulator mutation from NLP, support/healer behavior,
objective-control mode, PettingZoo, self-play, or advanced MARL.

Recommended next phase: Phase P11 Backend and Frontend Dashboard.
