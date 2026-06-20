export type ReplayShortcut =
  | { type: "toggle_play" }
  | { type: "reset" }
  | { type: "seek_relative"; seconds: number }
  | { type: "set_speed"; speed: number }
  | { type: "cycle_camera" }
  | { type: "toggle_follow" }
  | { type: "toggle_ranges" }
  | { type: "toggle_targets" };

export function replayShortcutForKey(key: string): ReplayShortcut | null {
  switch (key.toLowerCase()) {
    case " ":
      return { type: "toggle_play" };
    case "home":
      return { type: "reset" };
    case "arrowleft":
      return { type: "seek_relative", seconds: -1 };
    case "arrowright":
      return { type: "seek_relative", seconds: 1 };
    case "0":
      return { type: "set_speed", speed: 0.5 };
    case "1":
      return { type: "set_speed", speed: 1 };
    case "2":
      return { type: "set_speed", speed: 2 };
    case "4":
      return { type: "set_speed", speed: 4 };
    case "c":
      return { type: "cycle_camera" };
    case "f":
      return { type: "toggle_follow" };
    case "r":
      return { type: "toggle_ranges" };
    case "t":
      return { type: "toggle_targets" };
    default:
      return null;
  }
}

export function isEditableTarget(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (
    target.isContentEditable || target.matches("input, textarea, select, button")
  );
}
