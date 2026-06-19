import { describe, expect, it } from "vitest";

import { frameAtTime, interpolatePosition } from "../replay/interpolate";
import type { ReplayFrame } from "../replay/types";

const frames: ReplayFrame[] = [
  {
    replay_schema_version: "1.0",
    match_id: "match",
    tick: 0,
    sim_time_seconds: 0,
    agents: [
      { agent_id: "a", team_id: 0, role: "tank", position: [0, 0], hp: 100, max_hp: 100, alive: true },
    ],
  },
  {
    replay_schema_version: "1.0",
    match_id: "match",
    tick: 10,
    sim_time_seconds: 1,
    agents: [
      { agent_id: "a", team_id: 0, role: "tank", position: [10, 20], hp: 80, max_hp: 100, alive: true },
    ],
  },
];

describe("interpolation", () => {
  it("interpolates a position between two snapshots", () => {
    expect(interpolatePosition([0, 10], [10, 30], 0.25)).toEqual([2.5, 15]);
  });

  it("builds a smooth frame without inventing combat state", () => {
    const frame = frameAtTime(frames, 0.5);
    expect(frame.agents[0].position).toEqual([5, 10]);
    expect(frame.agents[0].hp).toBe(100);
    expect(frame.tick).toBe(5);
  });

  it("clamps to the last saved frame", () => {
    expect(frameAtTime(frames, 5).agents[0].hp).toBe(80);
  });
});
