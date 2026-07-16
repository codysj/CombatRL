import { describe, expect, it } from "vitest";

import { frameAtTime } from "../replay/interpolate";
import { parseJsonl } from "../replay/parseJsonl";
import type { ReplayFrame } from "../replay/types";
import { frame as fixtureFrame } from "./replayFixtures";

const PARSE_LINES = 20_000;
const FRAME_COUNT = 5_000;

describe("replay performance budgets", () => {
  it("parses a 20k-line JSONL stream within the local budget", () => {
    const text = Array.from(
      { length: PARSE_LINES },
      (_, index) => JSON.stringify({ tick: index, payload: "x".repeat(64) }),
    ).join("\n");
    const startedAt = performance.now();
    const parsed = parseJsonl<{ tick: number }>(text);
    const elapsedMs = performance.now() - startedAt;

    expect(parsed).toHaveLength(PARSE_LINES);
    expect(elapsedMs).toBeLessThan(1_500);
  });

  it("performs 10k timeline lookups across 5k frames within budget", () => {
    const frames: ReplayFrame[] = Array.from({ length: FRAME_COUNT }, (_, tick) => ({
      ...fixtureFrame,
      tick,
      sim_time_seconds: tick / 20,
    }));
    const startedAt = performance.now();
    for (let index = 0; index < 10_000; index += 1) {
      frameAtTime(frames, (index % FRAME_COUNT) / 20);
    }
    const elapsedMs = performance.now() - startedAt;

    expect(elapsedMs).toBeLessThan(1_000);
  });
});
