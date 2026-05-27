"""Behavior profile validation helpers."""

from pydantic import ValidationError

from combatrl.schemas.profiles import BehaviorProfile


def validate_profile(profile: BehaviorProfile) -> None:
    """Validate a profile object and raise a clear ValueError on failure."""
    try:
        BehaviorProfile.model_validate(profile.model_dump(mode="python"))
    except ValidationError as exc:
        msg = f"invalid behavior profile {profile.profile_id!r}: {exc}"
        raise ValueError(msg) from exc
