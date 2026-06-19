import type { ReplayEvent, ReplayFrame } from "./types";

export function replayDuration(frames: ReplayFrame[]): number {
  return frames.at(-1)?.sim_time_seconds ?? 0;
}

export function eventsThroughTick(events: ReplayEvent[], tick: number, limit = 12): ReplayEvent[] {
  const visible = events.filter((event) => event.tick <= tick);
  return visible.slice(Math.max(0, visible.length - limit)).reverse();
}

export function recentEvents(
  events: ReplayEvent[],
  timeSeconds: number,
  tickRateHz: number,
  windowSeconds = 0.45,
): ReplayEvent[] {
  const minTime = Math.max(0, timeSeconds - windowSeconds);
  return events.filter((event) => {
    const eventTime = event.tick / tickRateHz;
    return eventTime <= timeSeconds && eventTime >= minTime;
  });
}
