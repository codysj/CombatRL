from scripts.compare_profiles import run_profile_episode
from tests.integration.test_profile_comparisons import write_profile_test_scenario

from combatrl.replay.validators import validate_replay


def test_same_seed_same_profile_gives_same_replay_content(tmp_path) -> None:
    scenario = write_profile_test_scenario(tmp_path)
    _metrics_a, replay_a = run_profile_episode(
        scenario_path=scenario,
        profile_id="defensive",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=777,
        controlled_agent_id=None,
        replay_output_root=tmp_path / "a",
        max_ticks=30,
    )
    _metrics_b, replay_b = run_profile_episode(
        scenario_path=scenario,
        profile_id="defensive",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=777,
        controlled_agent_id=None,
        replay_output_root=tmp_path / "b",
        max_ticks=30,
    )

    assert replay_a is not None
    assert replay_b is not None
    assert (replay_a / "frames.jsonl").read_text(encoding="utf-8") == (
        replay_b / "frames.jsonl"
    ).read_text(encoding="utf-8")
    assert (replay_a / "events.jsonl").read_text(encoding="utf-8") == (
        replay_b / "events.jsonl"
    ).read_text(encoding="utf-8")
    assert (replay_a / "summary.json").read_text(encoding="utf-8") == (
        replay_b / "summary.json"
    ).read_text(encoding="utf-8")


def test_saved_profile_comparison_replay_validates(tmp_path) -> None:
    scenario = write_profile_test_scenario(tmp_path)
    _metrics, replay_path = run_profile_episode(
        scenario_path=scenario,
        profile_id="protective",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=778,
        controlled_agent_id=None,
        replay_output_root=tmp_path / "replay",
        max_ticks=30,
    )

    assert replay_path is not None
    validate_replay(replay_path)
