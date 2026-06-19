import type { AgentSnapshot, InterpolatedFrame, ReplayFrame, Vector2 } from "./types";

export function lerp(start: number, end: number, amount: number): number {
  return start + (end - start) * amount;
}

export function interpolatePosition(start: Vector2, end: Vector2, amount: number): Vector2 {
  return [lerp(start[0], end[0], amount), lerp(start[1], end[1], amount)];
}

export function interpolateAgent(
  start: AgentSnapshot,
  end: AgentSnapshot | undefined,
  amount: number,
): AgentSnapshot {
  if (!end) {
    return start;
  }

  const useEndState = amount >= 1;
  return {
    ...(useEndState ? end : start),
    position: interpolatePosition(start.position, end.position, amount),
  };
}

export function frameAtTime(frames: ReplayFrame[], timeSeconds: number): InterpolatedFrame {
  if (frames.length === 0) {
    throw new Error("Cannot interpolate an empty replay");
  }

  const clampedTime = Math.max(frames[0].sim_time_seconds, timeSeconds);
  let rightIndex = frames.findIndex((frame) => frame.sim_time_seconds >= clampedTime);
  if (rightIndex < 0) {
    rightIndex = frames.length - 1;
  }
  const leftIndex = Math.max(0, rightIndex - 1);
  const left = frames[leftIndex];
  const right = frames[rightIndex];
  const duration = right.sim_time_seconds - left.sim_time_seconds;
  const amount = duration <= 0 ? 0 : Math.min(1, (clampedTime - left.sim_time_seconds) / duration);
  const rightAgents = new Map(right.agents.map((agent) => [agent.agent_id, agent]));

  return {
    ...left,
    tick: Math.round(lerp(left.tick, right.tick, amount)),
    sim_time_seconds: Math.min(clampedTime, right.sim_time_seconds),
    agents: left.agents.map((agent) => interpolateAgent(agent, rightAgents.get(agent.agent_id), amount)),
    interpolation: amount,
  };
}
