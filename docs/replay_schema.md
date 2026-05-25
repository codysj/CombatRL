# CombatRL Replay Schema

Replay schema version: `1.0`

Replay artifacts are plain JSON and JSONL files under:

```text
artifacts/replays/
  <timestamp>_<scenario_id>_seed-<seed>/
    metadata.json
    frames.jsonl
    events.jsonl
    summary.json
```

## metadata.json

Written once at match start.

- `replay_schema_version`: replay schema version string.
- `match_id`: deterministic match ID.
- `scenario_id`: scenario ID from config.
- `seed`: match seed.
- `config`: full simulation config snapshot.
- `config_hash`: deterministic SHA-256 hash of the config snapshot.
- `tick_rate_hz`: simulation tick rate.
- `decision_rate_hz`: reserved for later agent decision cadence, currently `null`.
- `created_at_utc`: replay creation timestamp.
- `combatrl_version`: package version.

## frames.jsonl

One `ReplayFrame` JSON object per line. Frame ticks are strictly increasing and
start at tick `0`.

- `replay_schema_version`
- `match_id`
- `tick`
- `sim_time_seconds`
- `agents`: sorted by `agent_id`.
- `events`: events for this captured frame tick.
- `scoreboard`: `team0_alive`, `team1_alive`, `team0_total_hp`,
  `team1_total_hp`, `winner_team_id`, and `terminal_reason`.

Frame sampling may skip intermediate ticks when `--frame-interval` is greater
than `1`, but the final terminal frame is always written by the match script.

## events.jsonl

One `EventLog` JSON object per line. Events are recorded during simulator step
resolution and are not derived from replay frames.

Required event types currently emitted:

- `match_started`
- `agent_action_selected`
- `agent_moved`
- `agent_attacked`
- `agent_damaged`
- `agent_eliminated`
- `cooldown_started`
- `match_ended`

Event IDs are deterministic:

```text
<match_id>:tick-<tick>:event-<index>
```

## summary.json

Written once at match end.

- `replay_schema_version`
- `match_id`
- `scenario_id`
- `seed`
- `final_tick`
- `terminal`
- `terminal_reason`
- `winner_team_id`
- `frame_count`
- `event_count`
- `team0_alive`
- `team1_alive`
- `team0_total_hp`
- `team1_total_hp`

## Validation

Validate a replay with:

```powershell
uv run python scripts/validate_replay.py artifacts/replays/<replay-dir>
```

P7 can also generate a replay from the 2v2 Gymnasium environment:

```powershell
uv run python scripts/run_2v2_env_episode.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --seed 42 --policy random --save-replay
uv run python scripts/validate_replay.py <printed_replay_path>
```

The validator checks required files, schema validity, strictly increasing frame
ticks, event references, counts, event tick ranges, frame event tick agreement,
and final summary agreement with the final frame scoreboard.

## Rendering

Install renderer extras:

```powershell
uv sync --extra renderer
```

Render a replay:

```powershell
uv run python scripts/render_replay.py artifacts/replays/<replay-dir>
```

Controls:

- `Space`: pause/play
- `Right arrow`: step forward while paused
- `Left arrow`: step backward while paused
- `1`, `2`, `4`: speed controls
- `Esc` or window close: quit

Current limitations: playback is file-based, events are minimal debug events,
and the renderer is intentionally simple. Heuristic agents, Gymnasium, rewards,
training, behavior profiles, advanced metrics, support/healer mechanics,
objective control, and frontend/backend replay viewers are deferred.
