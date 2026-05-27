import json

from combatrl.nlp.parser import parse_command_to_profile


def test_parse_command_to_profile_defaults_to_rules() -> None:
    result = parse_command_to_profile("play aggressively")

    assert result.success
    assert result.parser_source == "rules"
    assert result.profile is not None


def test_fake_llm_valid_json_returns_validated_profile() -> None:
    def fake_llm(_prompt: str) -> str:
        return json.dumps({"profile": {"aggression": 0.8}, "unsupported_requests": []})

    result = parse_command_to_profile("play aggressively", use_llm=True, llm_client=fake_llm)

    assert result.success
    assert result.parser_source == "llm"
    assert result.profile is not None
    assert result.profile.aggression == 0.8


def test_fake_llm_invalid_json_fails_safely() -> None:
    result = parse_command_to_profile("play aggressively", use_llm=True, llm_client=lambda _: "[")

    assert not result.success
    assert result.profile is None


def test_fake_llm_unknown_fields_fail_safely() -> None:
    def fake_llm(_prompt: str) -> str:
        return json.dumps({"profile": {"aggression": 0.8, "raw_action_id": 9}})

    result = parse_command_to_profile("attack", use_llm=True, llm_client=fake_llm)

    assert not result.success
    assert any("unsupported profile field" in error for error in result.errors)


def test_use_llm_without_client_falls_back_to_rules() -> None:
    result = parse_command_to_profile("play aggressively", use_llm=True, llm_client=None)

    assert result.success
    assert result.parser_source == "fallback"
    assert result.profile is not None
