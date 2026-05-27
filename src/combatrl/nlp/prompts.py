"""Prompt templates for future structured-output LLM profile parsing."""

from __future__ import annotations

from combatrl.nlp.validation import PROFILE_AXIS_FIELDS, balanced_profile
from combatrl.schemas.profiles import BehaviorProfile

ALLOWED_PROFILE_FIELDS: tuple[str, ...] = (
    "profile_schema_version",
    "profile_id",
    *PROFILE_AXIS_FIELDS,
    "notes",
)
UNSUPPORTED_MECHANICS_EXAMPLES: tuple[str, ...] = (
    "teleport",
    "buy items",
    "shop",
    "farm minions",
    "fog or ambush from fog",
    "ward",
    "tower dive",
    "ultimate abilities",
    "heal or support/healer role",
    "revive",
    "summon",
    "build",
    "cast spells not in the current action system",
)

SYSTEM_PROMPT = """You translate CombatRL tactical language into a BehaviorProfile JSON object.
Output JSON only. Use only allowed BehaviorProfile fields and unsupported_requests.
Numeric profile values must be finite numbers from 0.0 to 1.0.
Do not output raw actions, action IDs, code, tool calls, or simulator commands.
Do not invent new abilities, items, roles, objectives, fog, healing, spells, or mechanics.
Unsupported requests must appear in unsupported_requests or short notes, not invented fields.
Tactical execution is handled elsewhere by the behavior modulation layer.
The LLM is only a translator from text to structured profile values."""


def build_profile_parser_prompt(
    command: str,
    base_profile: BehaviorProfile | None = None,
) -> str:
    """Build a deterministic structured-output prompt for an injected LLM client."""
    base = base_profile or balanced_profile()
    allowed_fields = ", ".join(ALLOWED_PROFILE_FIELDS)
    unsupported_examples = ", ".join(UNSUPPORTED_MECHANICS_EXAMPLES)
    base_axes = {axis: getattr(base, axis) for axis in PROFILE_AXIS_FIELDS}
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Allowed fields: {allowed_fields}\n"
        f"Allowed axes: {', '.join(PROFILE_AXIS_FIELDS)}\n"
        f"Unsupported mechanic examples: {unsupported_examples}\n"
        "Return this JSON shape exactly:\n"
        '{"profile": {"aggression": 0.5, "caution": 0.5, "cohesion": 0.5, '
        '"protectiveness": 0.5, "focus_fire": 0.5, "greed": 0.4, "spacing": 0.5, '
        '"objective_bias": 0.2}, "unsupported_requests": [], "notes": ""}\n\n'
        f"Base profile ID: {base.profile_id}\n"
        f"Base profile axes: {base_axes}\n"
        f"Command: {command}"
    )


__all__ = [
    "ALLOWED_PROFILE_FIELDS",
    "SYSTEM_PROMPT",
    "UNSUPPORTED_MECHANICS_EXAMPLES",
    "build_profile_parser_prompt",
]
