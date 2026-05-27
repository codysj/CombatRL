from combatrl.nlp.fallback_rules import parse_with_rules
from combatrl.nlp.validation import balanced_profile


def test_play_aggressively_increases_aggression_and_decreases_caution() -> None:
    base = balanced_profile()
    result = parse_with_rules("play aggressively", base)

    assert result.success
    assert result.profile is not None
    assert result.profile.aggression > base.aggression
    assert result.profile.caution < base.caution


def test_protect_ally_increases_protectiveness_and_cohesion() -> None:
    base = balanced_profile()
    result = parse_with_rules("protect ally", base)

    assert result.profile is not None
    assert result.profile.protectiveness > base.protectiveness
    assert result.profile.cohesion > base.cohesion


def test_kite_backward_and_avoid_close_combat_increases_spacing_and_caution() -> None:
    base = balanced_profile()
    result = parse_with_rules("kite backward and avoid close combat", base)

    assert result.profile is not None
    assert result.profile.spacing > base.spacing
    assert result.profile.caution > base.caution


def test_focus_same_target_increases_focus_fire() -> None:
    base = balanced_profile()
    result = parse_with_rules("focus the same target", base)

    assert result.profile is not None
    assert result.profile.focus_fire > base.focus_fire


def test_chase_low_health_enemies_increases_greed() -> None:
    base = balanced_profile()
    result = parse_with_rules("chase low health enemies", base)

    assert result.profile is not None
    assert result.profile.greed > base.greed


def test_stay_alive_increases_caution_and_decreases_greed_aggression() -> None:
    base = balanced_profile()
    result = parse_with_rules("stay alive", base)

    assert result.profile is not None
    assert result.profile.caution > base.caution
    assert result.profile.greed < base.greed
    assert result.profile.aggression < base.aggression


def test_unsupported_command_returns_unsupported_requests_and_does_not_crash() -> None:
    result = parse_with_rules("buy items and teleport")

    assert not result.success
    assert "buy items" in result.unsupported_requests
    assert "teleport" in result.unsupported_requests


def test_empty_command_fails_cleanly() -> None:
    result = parse_with_rules("  ")

    assert not result.success
    assert result.errors == ["command must be non-empty"]


def test_mixed_supported_and_unsupported_command_returns_profile_with_warning() -> None:
    result = parse_with_rules("play aggressive and teleport")

    assert result.success
    assert result.profile is not None
    assert "teleport" in result.unsupported_requests
    assert result.profile.aggression > balanced_profile().aggression
