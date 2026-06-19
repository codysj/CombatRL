import { describe, expect, it, vi } from "vitest";

import { loadReplay } from "../replay/loadReplay";

function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), { status });
}

describe("loadReplay", () => {
  it("loads metadata, frames, events, and summary", async () => {
    const fetcher = vi.fn((url: string | URL | Request) => {
      const path = String(url);
      if (path.endsWith("metadata.json")) return Promise.resolve(jsonResponse({ match_id: "m" }));
      if (path.endsWith("frames.jsonl")) {
        return Promise.resolve(new Response('{"tick":0,"sim_time_seconds":0,"agents":[]}\n'));
      }
      if (path.endsWith("events.jsonl")) return Promise.resolve(new Response(""));
      return Promise.resolve(jsonResponse({ final_tick: 0 }));
    }) as typeof fetch;

    const replay = await loadReplay("/demo/", fetcher);
    expect(replay.metadata.match_id).toBe("m");
    expect(replay.frames).toHaveLength(1);
    expect(replay.events).toEqual([]);
    expect(replay.summary.final_tick).toBe(0);
  });

  it("treats a missing optional event stream as empty", async () => {
    const fetcher = vi.fn((url: string | URL | Request) => {
      const path = String(url);
      if (path.endsWith("metadata.json")) return Promise.resolve(jsonResponse({}));
      if (path.endsWith("frames.jsonl")) {
        return Promise.resolve(new Response('{"tick":0,"sim_time_seconds":0,"agents":[]}'));
      }
      if (path.endsWith("events.jsonl")) return Promise.resolve(new Response("", { status: 404 }));
      return Promise.resolve(jsonResponse({}));
    }) as typeof fetch;

    await expect(loadReplay("/demo", fetcher)).resolves.toMatchObject({ events: [] });
  });
});
