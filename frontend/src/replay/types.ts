export type AgentRole = "tank" | "ranged_dps" | "support" | string;
export type Vector2 = [number, number];

export interface TeamAgentConfig {
  agent_id: string;
  team_id: number;
  role: AgentRole;
  spawn_position: Vector2;
}

export interface TeamConfig {
  team_id: number;
  agents: TeamAgentConfig[];
}

export interface ObstacleConfig {
  obstacle_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ReplayConfig {
  scenario_id?: string;
  arena_width?: number;
  arena_height?: number;
  max_ticks?: number;
  teams?: TeamConfig[];
  obstacles?: ObstacleConfig[];
  [key: string]: unknown;
}

export interface ReplayMetadata {
  replay_schema_version: string;
  match_id: string;
  scenario_id: string;
  seed: number;
  config: ReplayConfig;
  config_hash: string;
  tick_rate_hz: number;
  decision_rate_hz: number | null;
  created_at_utc: string;
  combatrl_version: string;
}

export interface ReplayEvent {
  event_id: string;
  tick: number;
  event_type: string;
  source_agent_id: string | null;
  target_agent_id: string | null;
  payload: Record<string, unknown>;
}

export interface AgentSnapshot {
  agent_id: string;
  team_id: number;
  role: AgentRole;
  position: Vector2;
  velocity?: Vector2;
  hp: number;
  max_hp: number;
  alive: boolean;
  movement_speed?: number;
  attack_range?: number;
  attack_damage?: number;
  attack_cooldown_ticks?: number;
  attack_cooldown_max_ticks?: number;
  ability_cooldown_ticks?: number;
  facing_vector?: Vector2;
  status_effects?: string[];
  current_target_id?: string | null;
  last_action_id?: number | null;
}

export interface ReplayFrame {
  replay_schema_version: string;
  match_id: string;
  tick: number;
  sim_time_seconds: number;
  agents: AgentSnapshot[];
  events?: ReplayEvent[];
  scoreboard?: Record<string, string | number | null>;
}

export interface ReplaySummary {
  replay_schema_version: string;
  match_id: string;
  scenario_id: string;
  seed: number;
  final_tick: number;
  terminal: boolean;
  terminal_reason: string | null;
  winner_team_id: number | null;
  frame_count: number;
  event_count: number;
  team0_alive: number;
  team1_alive: number;
  team0_total_hp: number;
  team1_total_hp: number;
}

export interface ReplayBundle {
  metadata: ReplayMetadata;
  frames: ReplayFrame[];
  events: ReplayEvent[];
  summary: ReplaySummary;
}

export interface InterpolatedFrame extends ReplayFrame {
  interpolation: number;
}
