from combatrl.nlp.parser import parse_command_to_profile
from combatrl.nlp.validation import balanced_profile, validate_parsed_profile


def test_missing_axes_are_filled_from_base_profile() -> None:
    base = balanced_profile()
    result = validate_parsed_profile(
        {"command": "be more aggressive", "aggression": 0.8},
        base_profile=base,
        parser_source="llm",
    )

    assert result.success
    assert result.profile is not None
    assert result.profile.aggression == 0.8
    assert result.profile.caution == base.caution


def test_unknown_llm_field_is_rejected() -> None:
    result = validate_parsed_profile(
        {"command": "teleport", "profile": {"aggression": 0.8, "teleport": 1.0}},
        base_profile=balanced_profile(),
        parser_source="llm",
    )

    assert not result.success
    assert any("unsupported profile field: teleport" in error for error in result.errors)


def test_out_of_range_llm_value_is_rejected() -> None:
    result = validate_parsed_profile(
        {"command": "attack", "aggression": 1.5},
        base_profile=balanced_profile(),
        parser_source="llm",
    )

    assert not result.success
    assert any("aggression must be between" in error for error in result.errors)


def test_out_of_range_rule_value_clamps_safely() -> None:
    result = validate_parsed_profile(
        {"command": "attack", "aggression": 1.5, "caution": -0.2},
        base_profile=balanced_profile(),
        parser_source="rules",
    )

    assert result.success
    assert result.profile is not None
    assert result.profile.aggression == 1.0
    assert result.profile.caution == 0.0


def test_invalid_json_returns_failure() -> None:
    result = parse_command_to_profile(
        "play aggressively",
        use_llm=True,
        llm_client=lambda _prompt: "{bad json",
    )

    assert not result.success
    assert result.parser_source == "llm"
    assert "invalid JSON" in result.errors[0]


def test_profile_id_is_deterministic_for_same_command_and_base() -> None:
    base = balanced_profile()
    first = validate_parsed_profile(
        {"command": "protect ally", "protectiveness": 0.8},
        base_profile=base,
        parser_source="llm",
    )
    second = validate_parsed_profile(
        {"command": "protect ally", "protectiveness": 0.8},
        base_profile=base,
        parser_source="llm",
    )

    assert first.profile is not None
    assert second.profile is not None
    assert first.profile.profile_id == second.profile.profile_id
