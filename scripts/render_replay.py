"""Render a CombatRL replay with the optional Pygame renderer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a CombatRL replay.")
    parser.add_argument("replay_path", type=Path)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument(
        "--overlays",
        type=str,
        default="hp_bars,attack_ranges,target_lines",
    )
    parser.add_argument("--headless-smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    overlays = [item.strip() for item in args.overlays.split(",") if item.strip()]
    try:
        from combatrl.renderer.pygame_renderer import render_replay

        render_replay(
            str(args.replay_path),
            playback_speed=args.speed,
            overlays=overlays,
            headless_smoke=args.headless_smoke,
        )
    except ModuleNotFoundError as exc:
        if exc.name == "pygame" or "renderer extras" in str(exc):
            print(
                "Pygame renderer dependency is not installed. "
                "Install renderer extras with: uv sync --extra renderer",
                file=sys.stderr,
            )
            return 1
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
