"""Validate a CombatRL replay artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from combatrl.replay.validators import validate_replay_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a CombatRL replay.")
    parser.add_argument("replay_path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_replay_report(args.replay_path)
    print(f"valid: {str(report['valid']).lower()}")
    print(f"match_id: {report['match_id']}")
    print(f"frames: {report['frames']}")
    print(f"events: {report['events']}")
    print(f"final_tick: {report['final_tick']}")
    print(f"terminal_reason: {report['terminal_reason']}")
    print(f"winner_team_id: {report['winner_team_id']}")
    if not report["valid"]:
        print(f"error: {report['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
