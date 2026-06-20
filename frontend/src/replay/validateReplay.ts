import type {
  AgentSnapshot,
  ReplayBundle,
  ReplayEvent,
  ReplayFrame,
  ReplayMetadata,
  ReplaySummary,
  Vector2,
} from "./types";

export const SUPPORTED_REPLAY_SCHEMA_VERSION = "1.0";

type JsonRecord = Record<string, unknown>;

function fail(location: string, message: string): never {
  throw new Error(`${location}: ${message}`);
}

function record(value: unknown, location: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    fail(location, "expected an object");
  }
  return value as JsonRecord;
}

function string(value: unknown, location: string): string {
  if (typeof value !== "string" || value.length === 0) fail(location, "expected a non-empty string");
  return value;
}

function nullableString(value: unknown, location: string): string | null {
  if (value === null) return null;
  return string(value, location);
}

function finiteNumber(value: unknown, location: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) fail(location, "expected a finite number");
  return value;
}

function nonNegativeNumber(value: unknown, location: string): number {
  const result = finiteNumber(value, location);
  if (result < 0) fail(location, "expected a non-negative number");
  return result;
}

function positiveNumber(value: unknown, location: string): number {
  const result = finiteNumber(value, location);
  if (result <= 0) fail(location, "expected a positive number");
  return result;
}

function integer(value: unknown, location: string): number {
  const result = nonNegativeNumber(value, location);
  if (!Number.isInteger(result)) fail(location, "expected a non-negative integer");
  return result;
}

function signedInteger(value: unknown, location: string): number {
  const result = finiteNumber(value, location);
  if (!Number.isInteger(result)) fail(location, "expected an integer");
  return result;
}

function boolean(value: unknown, location: string): boolean {
  if (typeof value !== "boolean") fail(location, "expected a boolean");
  return value;
}

function vector2(value: unknown, location: string): Vector2 {
  if (!Array.isArray(value) || value.length !== 2) fail(location, "expected a two-number vector");
  return [finiteNumber(value[0], `${location}[0]`), finiteNumber(value[1], `${location}[1]`)];
}

function schemaVersion(value: unknown, location: string): string {
  const version = string(value, location);
  if (version !== SUPPORTED_REPLAY_SCHEMA_VERSION) {
    fail(location, `unsupported replay schema version ${JSON.stringify(version)}; expected ${SUPPORTED_REPLAY_SCHEMA_VERSION}`);
  }
  return version;
}

export function parseJsonObject(text: string, filename: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`${filename}: invalid JSON: ${message}`);
  }
}

export function validateReplayMetadata(value: unknown, filename = "metadata.json"): ReplayMetadata {
  const item = record(value, filename);
  schemaVersion(item.replay_schema_version, `${filename}.replay_schema_version`);
  string(item.match_id, `${filename}.match_id`);
  string(item.scenario_id, `${filename}.scenario_id`);
  signedInteger(item.seed, `${filename}.seed`);
  string(item.config_hash, `${filename}.config_hash`);
  positiveNumber(item.tick_rate_hz, `${filename}.tick_rate_hz`);
  if (item.decision_rate_hz !== null) positiveNumber(item.decision_rate_hz, `${filename}.decision_rate_hz`);
  string(item.created_at_utc, `${filename}.created_at_utc`);
  string(item.combatrl_version, `${filename}.combatrl_version`);
  const config = record(item.config, `${filename}.config`);
  positiveNumber(config.arena_width, `${filename}.config.arena_width`);
  positiveNumber(config.arena_height, `${filename}.config.arena_height`);
  if (config.obstacles !== undefined && !Array.isArray(config.obstacles)) {
    fail(`${filename}.config.obstacles`, "expected an array");
  }
  return item as unknown as ReplayMetadata;
}

export function validateReplayEvent(
  value: unknown,
  location = "events.jsonl:line 1",
): ReplayEvent {
  const item = record(value, location);
  string(item.event_id, `${location}.event_id`);
  integer(item.tick, `${location}.tick`);
  string(item.event_type, `${location}.event_type`);
  nullableString(item.source_agent_id, `${location}.source_agent_id`);
  nullableString(item.target_agent_id, `${location}.target_agent_id`);
  record(item.payload, `${location}.payload`);
  return item as unknown as ReplayEvent;
}

function validateAgent(value: unknown, location: string): AgentSnapshot {
  const item = record(value, location);
  string(item.agent_id, `${location}.agent_id`);
  integer(item.team_id, `${location}.team_id`);
  string(item.role, `${location}.role`);
  vector2(item.position, `${location}.position`);
  const hp = nonNegativeNumber(item.hp, `${location}.hp`);
  const maxHp = positiveNumber(item.max_hp, `${location}.max_hp`);
  const alive = boolean(item.alive, `${location}.alive`);
  if (hp > maxHp) fail(`${location}.hp`, "cannot exceed max_hp");
  if (alive !== (hp > 0)) fail(`${location}.alive`, "must equal hp > 0");
  if (item.velocity !== undefined) vector2(item.velocity, `${location}.velocity`);
  if (item.facing_vector !== undefined) vector2(item.facing_vector, `${location}.facing_vector`);
  if (item.attack_range !== undefined) positiveNumber(item.attack_range, `${location}.attack_range`);
  if (item.current_target_id !== undefined) {
    nullableString(item.current_target_id, `${location}.current_target_id`);
  }
  if (item.status_effects !== undefined && !Array.isArray(item.status_effects)) {
    fail(`${location}.status_effects`, "expected an array");
  }
  return item as unknown as AgentSnapshot;
}

export function validateReplayFrame(value: unknown, lineNumber = 1): ReplayFrame {
  const location = `frames.jsonl:line ${lineNumber}`;
  const item = record(value, location);
  schemaVersion(item.replay_schema_version, `${location}.replay_schema_version`);
  string(item.match_id, `${location}.match_id`);
  integer(item.tick, `${location}.tick`);
  nonNegativeNumber(item.sim_time_seconds, `${location}.sim_time_seconds`);
  if (!Array.isArray(item.agents)) fail(`${location}.agents`, "expected an array");
  item.agents.forEach((agent, index) => validateAgent(agent, `${location}.agents[${index}]`));
  if (item.events !== undefined) {
    if (!Array.isArray(item.events)) fail(`${location}.events`, "expected an array");
    item.events.forEach((event, index) => validateReplayEvent(event, `${location}.events[${index}]`));
  }
  if (item.scoreboard !== undefined) record(item.scoreboard, `${location}.scoreboard`);
  return item as unknown as ReplayFrame;
}

export function validateReplaySummary(value: unknown, filename = "summary.json"): ReplaySummary {
  const item = record(value, filename);
  schemaVersion(item.replay_schema_version, `${filename}.replay_schema_version`);
  string(item.match_id, `${filename}.match_id`);
  string(item.scenario_id, `${filename}.scenario_id`);
  signedInteger(item.seed, `${filename}.seed`);
  integer(item.final_tick, `${filename}.final_tick`);
  boolean(item.terminal, `${filename}.terminal`);
  nullableString(item.terminal_reason, `${filename}.terminal_reason`);
  if (item.winner_team_id !== null) integer(item.winner_team_id, `${filename}.winner_team_id`);
  integer(item.frame_count, `${filename}.frame_count`);
  integer(item.event_count, `${filename}.event_count`);
  integer(item.team0_alive, `${filename}.team0_alive`);
  integer(item.team1_alive, `${filename}.team1_alive`);
  nonNegativeNumber(item.team0_total_hp, `${filename}.team0_total_hp`);
  nonNegativeNumber(item.team1_total_hp, `${filename}.team1_total_hp`);
  return item as unknown as ReplaySummary;
}

export function validateReplayBundle(bundle: ReplayBundle): ReplayBundle {
  const { metadata, frames, events, summary } = bundle;
  if (frames.length === 0) fail("frames.jsonl", "replay contains no frames");
  if (frames[0].tick !== 0) fail("frames.jsonl:line 1.tick", "first frame must start at tick 0");

  for (let index = 0; index < frames.length; index += 1) {
    const frame = frames[index];
    if (frame.match_id !== metadata.match_id) {
      fail(`frames.jsonl:line ${index + 1}.match_id`, "does not match metadata.json");
    }
    if (index > 0 && frame.tick <= frames[index - 1].tick) {
      fail(`frames.jsonl:line ${index + 1}.tick`, "frame ticks must be strictly increasing");
    }
  }

  events.forEach((event, index) => {
    if (event.tick > summary.final_tick) {
      fail(`events.jsonl:line ${index + 1}.tick`, "cannot exceed summary final_tick");
    }
  });

  if (summary.match_id !== metadata.match_id) fail("summary.json.match_id", "does not match metadata.json");
  if (summary.scenario_id !== metadata.scenario_id) fail("summary.json.scenario_id", "does not match metadata.json");
  if (summary.seed !== metadata.seed) fail("summary.json.seed", "does not match metadata.json");
  if (summary.frame_count !== frames.length) fail("summary.json.frame_count", `expected ${frames.length}`);
  if (summary.event_count !== events.length) fail("summary.json.event_count", `expected ${events.length}`);
  if (summary.final_tick !== frames.at(-1)?.tick) fail("summary.json.final_tick", "does not match the final frame");
  return bundle;
}
