"""CLI for training the CombatRL PPO baseline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from combatrl.training.train_ppo import train_ppo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a CombatRL PPO baseline.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/training/ppo_1v1_baseline.yaml"),
    )
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--total-timesteps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config
    temp_config_path: Path | None = None
    if args.total_timesteps is not None or args.seed is not None:
        temp_config_path = _override_config(args)
        config_path = temp_config_path

    try:
        run_dir = train_ppo(config_path, smoke=args.smoke)
    except Exception as exc:
        print(f"train_ppo failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if temp_config_path is not None:
            temp_config_path.unlink(missing_ok=True)

    final_checkpoint = run_dir / "model_final.zip"
    best_checkpoint = run_dir / "best_model.zip"
    print(f"run_dir: {run_dir}")
    print(f"model_final: {final_checkpoint}")
    print(f"best_model: {best_checkpoint if best_checkpoint.exists() else None}")
    print(f"config: {run_dir / 'config.yaml'}")
    print(f"metadata: {run_dir / 'model_metadata.json'}")
    print(f"metrics: {run_dir / 'metrics.json'}")
    print(f"evaluation: {run_dir / 'evaluation_metrics.json'}")
    return 0


def _override_config(args: argparse.Namespace) -> Path:
    payload = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.total_timesteps is not None:
        key = "smoke_total_timesteps" if args.smoke else "total_timesteps"
        payload[key] = args.total_timesteps
    if args.seed is not None:
        payload["seed"] = args.seed
    temp_path = args.config.parent / f".{args.config.stem}_override.yaml"
    temp_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return temp_path


if __name__ == "__main__":
    raise SystemExit(main())
