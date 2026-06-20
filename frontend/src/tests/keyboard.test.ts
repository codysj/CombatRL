import { describe, expect, it } from "vitest";

import { replayShortcutForKey } from "../replay/keyboard";

describe("replay keyboard shortcuts", () => {
  it("maps playback, camera, and overlay shortcuts", () => {
    expect(replayShortcutForKey(" ")).toEqual({ type: "toggle_play" });
    expect(replayShortcutForKey("ArrowRight")).toEqual({ type: "seek_relative", seconds: 1 });
    expect(replayShortcutForKey("4")).toEqual({ type: "set_speed", speed: 4 });
    expect(replayShortcutForKey("C")).toEqual({ type: "cycle_camera" });
    expect(replayShortcutForKey("f")).toEqual({ type: "toggle_follow" });
  });

  it("ignores unrelated keys", () => {
    expect(replayShortcutForKey("Escape")).toBeNull();
  });
});
