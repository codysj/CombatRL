"""Parse a natural-language command into a validated CombatRL behavior profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from combatrl.nlp.parser import parse_command_to_profile
from combatrl.profiles.loader import load_profile_by_id
from combatrl.schemas.nlp import BehaviorProfileParseResult
from combatrl.schemas.profiles import BehaviorProfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse a tactical command into a BehaviorProfile.")
    parser.add_argument("command_parts", nargs="*", help="Command text to parse.")
    parser.add_argument("--command", default=None, help="Command text to parse.")
    parser.add_argument("--base-profile", default="balanced")
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--output-profile", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = args.command if args.command is not None else " ".join(args.command_parts)
    try:
        base_profile = load_profile_by_id(args.base_profile)
    except Exception as exc:
        print(f"parse_command failed: could not load base profile: {exc}", file=sys.stderr)
        return 1

    result = parse_command_to_profile(
        command,
        base_profile=base_profile,
        use_llm=args.use_llm,
        llm_client=None,
    )
    if args.output_profile is not None and result.success and result.profile is not None:
        _write_profile(args.output_profile, result.profile)

    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        _print_human_summary(result)
        if args.output_profile is not None and result.success:
            print(f"output_profile_path: {args.output_profile}")
    return 0 if result.success else 1


def _write_profile(path: Path, profile: BehaviorProfile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = profile.model_dump(mode="json")
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _print_human_summary(result: BehaviorProfileParseResult) -> None:
    print(f"success: {str(result.success).lower()}")
    print(f"parser_source: {result.parser_source}")
    print(f"command: {result.command}")
    if result.profile is not None:
        print(f"profile_id: {result.profile.profile_id}")
        for field_name in (
            "aggression",
            "caution",
            "cohesion",
            "protectiveness",
            "focus_fire",
            "greed",
            "spacing",
            "objective_bias",
        ):
            print(f"{field_name}: {getattr(result.profile, field_name):.3f}")
    print(f"unsupported_requests: {result.unsupported_requests}")
    print(f"errors: {result.errors}")
    print(f"notes: {result.notes}")


if __name__ == "__main__":
    raise SystemExit(main())
