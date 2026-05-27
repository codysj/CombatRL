"""Validation and repair helpers for parsed behavior profiles."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from pydantic import ValidationError

from combatrl.core.constants import PROFILE_SCHEMA_VERSION
from combatrl.schemas.nlp import BehaviorProfileParseResult, ParserSource
from combatrl.schemas.profiles import BehaviorProfile

PROFILE_AXIS_FIELDS: tuple[str, ...] = (
    "aggression",
    "caution",
    "cohesion",
    "protectiveness",
    "focus_fire",
    "greed",
    "spacing",
    "objective_bias",
)
PROFILE_FIELDS = frozenset(BehaviorProfile.model_fields)
ENVELOPE_FIELDS = frozenset({"command", "profile", "unsupported_requests", "notes"})

UNSUPPORTED_MECHANICS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("teleport", (r"\bteleport\b", r"\bblink\b")),
    ("buy items", (r"\bbuy\s+items?\b", r"\bpurchase\s+items?\b")),
    ("shop", (r"\bshop\b", r"\bshopping\b")),
    ("farm minions", (r"\bfarm\s+minions?\b", r"\bminions?\b", r"\blane\b")),
    ("fog", (r"\bfog\b", r"\bfog\s+of\s+war\b")),
    ("ambush from fog", (r"\bambush\s+from\s+fog\b", r"\bgank\s+from\s+fog\b")),
    ("ward", (r"\bward\b", r"\bwards\b", r"\bvision\s+ward\b")),
    ("tower dive", (r"\btower\s+dive\b", r"\bturret\s+dive\b")),
    ("ultimate", (r"\bultimate\b", r"\bult\b", r"\bults\b")),
    ("heal", (r"\bheal\b", r"\bhealer\b", r"\bsupport\b")),
    ("revive", (r"\brevive\b", r"\bresurrect\b")),
    ("summon", (r"\bsummon\b", r"\bspawn\s+pet\b")),
    ("build", (r"\bbuild\b", r"\bconstruct\b")),
    ("cast spell", (r"\bcast\s+\w+\b", r"\bspell\b", r"\bfireball\b")),
)


def validate_parsed_profile(
    candidate: dict[str, Any],
    base_profile: BehaviorProfile | None = None,
    parser_source: ParserSource = "fallback",
) -> BehaviorProfileParseResult:
    """Validate an untrusted profile candidate into a bounded BehaviorProfile."""
    command = str(candidate.get("command", ""))
    unsupported_requests = _normalize_string_list(candidate.get("unsupported_requests", []))
    unsupported_requests.extend(detect_unsupported_requests(command))
    unsupported_requests = _dedupe(unsupported_requests)

    profile_candidate, envelope_errors = _extract_profile_candidate(candidate)
    errors = list(envelope_errors)
    base = base_profile or balanced_profile()
    merged = merge_with_base_profile(profile_candidate, base)
    explicit_schema_version = profile_candidate.get("profile_schema_version")
    if (
        explicit_schema_version is not None
        and parser_source != "rules"
        and explicit_schema_version != PROFILE_SCHEMA_VERSION
    ):
        errors.append(f"profile_schema_version must be {PROFILE_SCHEMA_VERSION}")
    merged["profile_schema_version"] = PROFILE_SCHEMA_VERSION
    merged["profile_id"] = deterministic_profile_id(command, base)
    notes = _clean_notes(profile_candidate.get("notes") or candidate.get("notes"))
    if notes is not None:
        merged["notes"] = notes

    for axis in PROFILE_AXIS_FIELDS:
        value = merged.get(axis)
        if not isinstance(value, int | float) or isinstance(value, bool):
            errors.append(f"{axis} must be numeric")
            continue
        if not math.isfinite(float(value)):
            errors.append(f"{axis} must be finite")
            continue
        if parser_source == "rules":
            merged[axis] = _clamp(float(value))
        elif not 0.0 <= float(value) <= 1.0:
            errors.append(f"{axis} must be between 0.0 and 1.0")

    if errors:
        return BehaviorProfileParseResult(
            success=False,
            command=command,
            profile=None,
            errors=errors,
            unsupported_requests=unsupported_requests,
            parser_source=parser_source,
            notes=notes,
        )

    try:
        profile = BehaviorProfile.model_validate(merged)
    except ValidationError as exc:
        return BehaviorProfileParseResult(
            success=False,
            command=command,
            profile=None,
            errors=[_format_validation_error(exc)],
            unsupported_requests=unsupported_requests,
            parser_source=parser_source,
            notes=notes,
        )

    return BehaviorProfileParseResult(
        success=True,
        command=command,
        profile=profile,
        errors=[],
        unsupported_requests=unsupported_requests,
        parser_source=parser_source,
        notes=notes,
    )


def sanitize_profile_id(text: str) -> str:
    """Return a stable, filesystem-safe profile ID fragment."""
    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return normalized[:48] or "command"


def merge_with_base_profile(
    candidate: dict[str, Any],
    base_profile: BehaviorProfile,
) -> dict[str, Any]:
    """Fill missing profile fields from a base profile."""
    merged = base_profile.model_dump(mode="python")
    for field_name, value in candidate.items():
        if field_name in PROFILE_FIELDS:
            merged[field_name] = value
    return merged


def detect_unsupported_requests(command: str) -> list[str]:
    """Detect unsupported mechanics in a command without raising."""
    normalized = command.lower()
    unsupported: list[str] = []
    for label, patterns in UNSUPPORTED_MECHANICS:
        if any(re.search(pattern, normalized) for pattern in patterns):
            unsupported.append(label)
    return _dedupe(unsupported)


def balanced_profile() -> BehaviorProfile:
    """Return the built-in balanced profile without reading config files."""
    return BehaviorProfile(
        profile_schema_version=PROFILE_SCHEMA_VERSION,
        profile_id="balanced",
        aggression=0.50,
        caution=0.50,
        cohesion=0.50,
        protectiveness=0.50,
        focus_fire=0.50,
        greed=0.40,
        spacing=0.50,
        objective_bias=0.20,
        notes="Balanced tactical profile for baseline comparisons.",
    )


def deterministic_profile_id(command: str, base_profile: BehaviorProfile) -> str:
    """Generate the required deterministic generated profile ID."""
    payload = "|".join(
        [
            command,
            base_profile.profile_id,
            *(f"{axis}={getattr(base_profile, axis):.6f}" for axis in PROFILE_AXIS_FIELDS),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"generated_from_command_{digest}"


def _extract_profile_candidate(candidate: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    top_level_unknown = sorted(set(candidate) - PROFILE_FIELDS - ENVELOPE_FIELDS)
    for field_name in top_level_unknown:
        errors.append(f"unsupported profile field: {field_name}")

    raw_profile = candidate.get("profile")
    if raw_profile is None:
        raw_profile = {key: value for key, value in candidate.items() if key in PROFILE_FIELDS}
    elif not isinstance(raw_profile, dict):
        errors.append("profile must be an object")
        raw_profile = {}

    profile_candidate: dict[str, Any] = dict(raw_profile)
    nested_unknown = sorted(set(profile_candidate) - PROFILE_FIELDS)
    for field_name in nested_unknown:
        errors.append(f"unsupported profile field: {field_name}")
        profile_candidate.pop(field_name, None)
    return profile_candidate, errors


def _clean_notes(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for unsupported in detect_unsupported_requests(text):
        if "unsupported" not in text.lower():
            return f"Unsupported request noted: {unsupported}."
    return text[:180]


def _normalize_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            deduped.append(normalized)
            seen.add(key)
    return deduped


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _format_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"])
        parts.append(f"{location}: {error['msg']}")
    return "; ".join(parts)


__all__ = [
    "PROFILE_AXIS_FIELDS",
    "balanced_profile",
    "detect_unsupported_requests",
    "deterministic_profile_id",
    "merge_with_base_profile",
    "sanitize_profile_id",
    "validate_parsed_profile",
]
