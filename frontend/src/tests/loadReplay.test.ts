import { describe, expect, it, vi } from "vitest";

import {
  loadReplay,
  loadReplayFiles,
  loadReplayTexts,
  type ReplayFile,
  type ReplayFilename,
} from "../replay/loadReplay";
import { replayTexts } from "./replayFixtures";

function responseMap(texts: Record<ReplayFilename, string>): typeof fetch {
  return vi.fn((url: string | URL | Request) => {
    const filename = String(url).split("/").at(-1) as ReplayFilename;
    return Promise.resolve(new Response(texts[filename]));
  }) as typeof fetch;
}

function localFiles(texts: Record<ReplayFilename, string>): ReplayFile[] {
  return Object.entries(texts).map(([name, text]) => ({
    name,
    webkitRelativePath: `sample-replay/${name}`,
    text: () => Promise.resolve(text),
  }));
}

describe("loadReplay", () => {
  it("loads and validates metadata, frames, events, and summary", async () => {
    const replay = await loadReplay("/demo/", responseMap(replayTexts()));
    expect(replay.metadata.match_id).toBe("match-1");
    expect(replay.frames).toHaveLength(1);
    expect(replay.events).toHaveLength(1);
    expect(replay.summary.final_tick).toBe(0);
  });

  it("reports a missing required static file", async () => {
    const fetcher = vi.fn((url: string | URL | Request) => {
      const filename = String(url).split("/").at(-1) as ReplayFilename;
      return Promise.resolve(filename === "events.jsonl"
        ? new Response("", { status: 404 })
        : new Response(replayTexts()[filename]));
    }) as typeof fetch;

    await expect(loadReplay("/demo", fetcher)).rejects.toThrow("events.jsonl");
  });
});

describe("loadReplayFiles", () => {
  it("loads one user-selected replay directory and returns its label", async () => {
    const loaded = await loadReplayFiles(localFiles(replayTexts()));
    expect(loaded.label).toBe("sample-replay");
    expect(loaded.replay.metadata.scenario_id).toBe("test-scenario");
  });

  it("reports every missing core replay file", async () => {
    const files = localFiles(replayTexts()).filter((file) =>
      file.name !== "events.jsonl" && file.name !== "summary.json");
    await expect(loadReplayFiles(files)).rejects.toThrow("events.jsonl, summary.json");
  });

  it("rejects a parent directory containing multiple replays", async () => {
    const files = localFiles(replayTexts());
    files.push({ name: "metadata.json", text: () => Promise.resolve(replayTexts()["metadata.json"]) });
    await expect(loadReplayFiles(files)).rejects.toThrow("multiple metadata.json");
  });
});

describe("loadReplayTexts", () => {
  it("reports malformed JSONL with its filename and line", () => {
    expect(() => loadReplayTexts(replayTexts({ "frames.jsonl": "not-json" })))
      .toThrow("frames.jsonl:line 1: invalid JSON");
  });
});
