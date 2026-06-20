import { parseJsonl } from "./parseJsonl";
import type { ReplayBundle, ReplayEvent, ReplayFrame } from "./types";
import {
  parseJsonObject,
  validateReplayBundle,
  validateReplayEvent,
  validateReplayFrame,
  validateReplayMetadata,
  validateReplaySummary,
} from "./validateReplay";

export const REPLAY_FILENAMES = ["metadata.json", "frames.jsonl", "events.jsonl", "summary.json"] as const;
export type ReplayFilename = typeof REPLAY_FILENAMES[number];

export interface ReplayFile {
  name: string;
  webkitRelativePath?: string;
  text: () => Promise<string>;
}

export interface LoadedLocalReplay {
  replay: ReplayBundle;
  label: string;
}

async function fetchRequired(response: Promise<Response>, filename: ReplayFilename): Promise<Response> {
  const resolved = await response;
  if (!resolved.ok) throw new Error(`${filename}: unable to load file (HTTP ${resolved.status})`);
  return resolved;
}

export function loadReplayTexts(files: Record<ReplayFilename, string>): ReplayBundle {
  const metadata = validateReplayMetadata(parseJsonObject(files["metadata.json"], "metadata.json"));
  const frames = parseJsonl<ReplayFrame>(files["frames.jsonl"], {
    filename: "frames.jsonl",
    validate: validateReplayFrame,
  });
  const events = parseJsonl<ReplayEvent>(files["events.jsonl"], {
    filename: "events.jsonl",
    validate: (value, lineNumber) => validateReplayEvent(value, `events.jsonl:line ${lineNumber}`),
  });
  const summary = validateReplaySummary(parseJsonObject(files["summary.json"], "summary.json"));
  return validateReplayBundle({ metadata, frames, events, summary });
}

export async function loadReplay(baseUrl: string, fetcher: typeof fetch = fetch): Promise<ReplayBundle> {
  const normalizedBase = baseUrl.replace(/\/$/, "");
  const responses = await Promise.all(REPLAY_FILENAMES.map((filename) =>
    fetchRequired(fetcher(`${normalizedBase}/${filename}`), filename),
  ));
  const contents = await Promise.all(responses.map((response) => response.text()));
  const files = Object.fromEntries(REPLAY_FILENAMES.map((filename, index) => [filename, contents[index]])) as
    Record<ReplayFilename, string>;
  return loadReplayTexts(files);
}

export async function loadReplayFiles(selectedFiles: Iterable<ReplayFile>): Promise<LoadedLocalReplay> {
  const files = new Map<ReplayFilename, ReplayFile>();
  for (const file of selectedFiles) {
    if (!REPLAY_FILENAMES.includes(file.name as ReplayFilename)) continue;
    const filename = file.name as ReplayFilename;
    if (files.has(filename)) {
      throw new Error(`Selected directory contains multiple ${filename} files; select one replay directory`);
    }
    files.set(filename, file);
  }

  const missing = REPLAY_FILENAMES.filter((filename) => !files.has(filename));
  if (missing.length > 0) throw new Error(`Replay directory is incomplete; missing ${missing.join(", ")}`);

  const contents = await Promise.all(REPLAY_FILENAMES.map((filename) => files.get(filename)!.text()));
  const texts = Object.fromEntries(REPLAY_FILENAMES.map((filename, index) => [filename, contents[index]])) as
    Record<ReplayFilename, string>;
  const firstFile = files.get("metadata.json")!;
  const relativePath = firstFile.webkitRelativePath ?? "";
  const label = relativePath.includes("/") ? relativePath.split("/").at(-2)! : "Local replay";
  return { replay: loadReplayTexts(texts), label };
}
