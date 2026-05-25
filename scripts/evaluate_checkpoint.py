"""CLI for evaluating a saved CombatRL PPO checkpoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from combatrl.training.evaluate_checkpoint import evaluate_checkpoint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a CombatRL PPO checkpoint.")
    parser.add_argument("checkpoint_path", type=Path)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=1000)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--deterministic", action="store_true", default=True)
    mode.add_argument("--stochastic", action="store_true")
    parser.add_argument("--save-replay", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        metrics = evaluate_checkpoint(
            args.checkpoint_path,
            args.env_config,
            num_episodes=args.episodes,
            seed_start=args.seed_start,
            deterministic=not args.stochastic,
            save_replay=args.save_replay,
        )
    except Exception as exc:
        print(f"evaluate_checkpoint failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
