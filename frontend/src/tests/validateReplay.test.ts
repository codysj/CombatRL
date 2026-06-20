import { describe, expect, it } from "vitest";

import { loadReplayTexts } from "../replay/loadReplay";
import { frame, metadata, replayTexts, summary } from "./replayFixtures";

describe("replay runtime validation", () => {
  it("rejects unsupported schema versions with a clear error", () => {
    const unsupported = { ...metadata, replay_schema_version: "2.0" };
    expect(() => loadReplayTexts(replayTexts({ "metadata.json": JSON.stringify(unsupported) })))
      .toThrow('unsupported replay schema version "2.0"');
  });

  it("reports invalid agent fields at the JSONL line", () => {
    const invalidFrame = { ...frame, agents: [{ ...frame.agents[0], position: [10] }] };
    expect(() => loadReplayTexts(replayTexts({ "frames.jsonl": JSON.stringify(invalidFrame) })))
      .toThrow("frames.jsonl:line 1.agents[0].position");
  });

  it("rejects inconsistent frame counts", () => {
    const invalidSummary = { ...summary, frame_count: 2 };
    expect(() => loadReplayTexts(replayTexts({ "summary.json": JSON.stringify(invalidSummary) })))
      .toThrow("summary.json.frame_count: expected 1");
  });

  it("rejects mismatched replay identities", () => {
    const invalidSummary = { ...summary, match_id: "another-match" };
    expect(() => loadReplayTexts(replayTexts({ "summary.json": JSON.stringify(invalidSummary) })))
      .toThrow("summary.json.match_id");
  });
});
