import type { ReplayMetadata, Vector2 } from "../replay/types";

export interface ArenaDimensions {
  width: number;
  height: number;
}

export function getArenaDimensions(metadata: ReplayMetadata): ArenaDimensions {
  return {
    width: metadata.config.arena_width ?? 100,
    height: metadata.config.arena_height ?? 60,
  };
}

export function simulationToWorld(position: Vector2, arena: ArenaDimensions): [number, number, number] {
  return [position[0] - arena.width / 2, 0, position[1] - arena.height / 2];
}
