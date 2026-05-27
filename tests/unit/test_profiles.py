import pytest
from pydantic import ValidationError

from combatrl.schemas.profiles import BehaviorProfile


def valid_profile_data() -> dict[str, object]:
    return {
        "profile_schema_version": "1.0",
        "profile_id": "test",
        "aggression": 0.5,
        "caution": 0.5,
        "cohesion": 0.5,
        "protectiveness": 0.5,
        "focus_fire": 0.5,
        "greed": 0.5,
        "spacing": 0.5,
        "objective_bias": 0.2,
    }


def test_behavior_profile_accepts_valid_numeric_axes() -> None:
    profile = BehaviorProfile.model_validate(valid_profile_data())

    assert profile.profile_id == "test"
    assert profile.aggression == 0.5


@pytest.mark.parametrize(("field_name", "value"), [("aggression", -0.01), ("caution", 1.01)])
def test_behavior_profile_rejects_out_of_range_axes(field_name: str, value: float) -> None:
    data = valid_profile_data()
    data[field_name] = value

    with pytest.raises(ValidationError):
        BehaviorProfile.model_validate(data)


def test_behavior_profile_requires_non_empty_profile_id() -> None:
    data = valid_profile_data()
    data["profile_id"] = " "

    with pytest.raises(ValidationError, match="profile_id must be non-empty"):
        BehaviorProfile.model_validate(data)


def test_behavior_profile_defaults_schema_version_for_programmatic_profiles() -> None:
    data = valid_profile_data()
    data.pop("profile_schema_version")

    profile = BehaviorProfile.model_validate(data)

    assert profile.profile_schema_version == "1.0"
