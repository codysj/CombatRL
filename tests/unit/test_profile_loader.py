import pytest

from combatrl.profiles.loader import list_profiles, load_profile, load_profile_by_id


def test_valid_profile_yaml_loads() -> None:
    profile = load_profile("configs/profiles/aggressive.yaml")

    assert profile.profile_id == "aggressive"
    assert profile.aggression == 0.90


def test_invalid_value_below_zero_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
profile_schema_version: "1.0"
profile_id: bad
aggression: -0.1
caution: 0.5
cohesion: 0.5
protectiveness: 0.5
focus_fire: 0.5
greed: 0.5
spacing: 0.5
objective_bias: 0.2
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="aggression"):
        load_profile(path)


def test_invalid_value_above_one_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
profile_schema_version: "1.0"
profile_id: bad
aggression: 0.5
caution: 1.1
cohesion: 0.5
protectiveness: 0.5
focus_fire: 0.5
greed: 0.5
spacing: 0.5
objective_bias: 0.2
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="caution"):
        load_profile(path)


def test_missing_axis_fails(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
profile_schema_version: "1.0"
profile_id: bad
aggression: 0.5
caution: 0.5
cohesion: 0.5
protectiveness: 0.5
focus_fire: 0.5
greed: 0.5
objective_bias: 0.2
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="spacing"):
        load_profile(path)


def test_missing_schema_version_fails_for_yaml(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
profile_id: bad
aggression: 0.5
caution: 0.5
cohesion: 0.5
protectiveness: 0.5
focus_fire: 0.5
greed: 0.5
spacing: 0.5
objective_bias: 0.2
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="profile_schema_version"):
        load_profile(path)


def test_list_profiles_returns_expected_presets() -> None:
    assert list_profiles() == [
        "aggressive",
        "balanced",
        "defensive",
        "kiter",
        "protective",
    ]


def test_load_profile_by_id_uses_preset_directory() -> None:
    profile = load_profile_by_id("protective")

    assert profile.profile_id == "protective"
