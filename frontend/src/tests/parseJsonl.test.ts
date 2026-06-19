import { describe, expect, it } from "vitest";

import { parseJsonl } from "../replay/parseJsonl";
import type { ReplayFrame } from "../replay/types";

describe("parseJsonl", () => {
  it("parses frame objects and ignores blank lines", () => {
    const frames = parseJsonl<ReplayFrame>(
      '{"tick":0,"sim_time_seconds":0,"agents":[]}\n\n{"tick":4,"sim_time_seconds":0.2,"agents":[]}\n',
    );

    expect(frames).toHaveLength(2);
    expect(frames[1].tick).toBe(4);
  });

  it("reports the line containing invalid JSON", () => {
    expect(() => parseJsonl('{"tick":0}\nnot-json')).toThrow("line 2");
  });

  it("does not require optional replay fields at parse time", () => {
    expect(parseJsonl<ReplayFrame>('{"tick":0,"sim_time_seconds":0,"agents":[]}')).toHaveLength(1);
  });
});
