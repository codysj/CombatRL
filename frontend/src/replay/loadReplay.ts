import { parseJsonl } from "./parseJsonl";
import type {
  ReplayBundle,
  ReplayEvent,
  ReplayFrame,
  ReplayMetadata,
  ReplaySummary,
} from "./types";

async function fetchRequired(response: Promise<Response>, filename: string): Promise<Response> {
  const resolved = await response;
  if (!resolved.ok) {
    throw new Error(`Unable to load ${filename} (${resolved.status})`);
  }
  return resolved;
}

export async function loadReplay(baseUrl: string, fetcher: typeof fetch = fetch): Promise<ReplayBundle> {
  const normalizedBase = baseUrl.replace(/\/$/, "");
  const [metadataResponse, framesResponse, eventsResponse, summaryResponse] = await Promise.all([
    fetchRequired(fetcher(`${normalizedBase}/metadata.json`), "metadata.json"),
    fetchRequired(fetcher(`${normalizedBase}/frames.jsonl`), "frames.jsonl"),
    fetcher(`${normalizedBase}/events.jsonl`),
    fetchRequired(fetcher(`${normalizedBase}/summary.json`), "summary.json"),
  ]);

  const [metadata, framesText, eventsText, summary] = await Promise.all([
    metadataResponse.json() as Promise<ReplayMetadata>,
    framesResponse.text(),
    eventsResponse.ok ? eventsResponse.text() : Promise.resolve(""),
    summaryResponse.json() as Promise<ReplaySummary>,
  ]);

  const frames = parseJsonl<ReplayFrame>(framesText).sort((a, b) => a.tick - b.tick);
  if (frames.length === 0) {
    throw new Error("Replay contains no frames");
  }

  return {
    metadata,
    frames,
    events: parseJsonl<ReplayEvent>(eventsText).sort((a, b) => a.tick - b.tick),
    summary,
  };
}
