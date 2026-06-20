import type { ReplayBundle, ReplayEvent, ReplayFrame, ReplayMetadata, ReplaySummary } from "../replay/types";
import type { ReplayFilename } from "../replay/loadReplay";

export const metadata: ReplayMetadata = {
  replay_schema_version: "1.0",
  match_id: "match-1",
  scenario_id: "test-scenario",
  seed: 7,
  config: { arena_width: 100, arena_height: 60, obstacles: [] },
  config_hash: "hash",
  tick_rate_hz: 20,
  decision_rate_hz: null,
  created_at_utc: "2026-06-19T00:00:00Z",
  combatrl_version: "0.1.0",
};

export const frame: ReplayFrame = {
  replay_schema_version: "1.0",
  match_id: "match-1",
  tick: 0,
  sim_time_seconds: 0,
  agents: [{
    agent_id: "team0_tank_0",
    team_id: 0,
    role: "tank",
    position: [10, 20],
    hp: 100,
    max_hp: 100,
    alive: true,
  }],
  events: [],
  scoreboard: {},
};

export const event: ReplayEvent = {
  event_id: "match-1:tick-0:event-0",
  tick: 0,
  event_type: "match_started",
  source_agent_id: null,
  target_agent_id: null,
  payload: {},
};

export const summary: ReplaySummary = {
  replay_schema_version: "1.0",
  match_id: "match-1",
  scenario_id: "test-scenario",
  seed: 7,
  final_tick: 0,
  terminal: true,
  terminal_reason: "elimination",
  winner_team_id: 0,
  frame_count: 1,
  event_count: 1,
  team0_alive: 1,
  team1_alive: 0,
  team0_total_hp: 100,
  team1_total_hp: 0,
};

export const bundle: ReplayBundle = { metadata, frames: [frame], events: [event], summary };

export function replayTexts(overrides: Partial<Record<ReplayFilename, string>> = {}): Record<ReplayFilename, string> {
  return {
    "metadata.json": JSON.stringify(metadata),
    "frames.jsonl": JSON.stringify(frame),
    "events.jsonl": JSON.stringify(event),
    "summary.json": JSON.stringify(summary),
    ...overrides,
  };
}
