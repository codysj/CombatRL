import json

from tests.integration.bot_match_helpers import run_bot_match

from combatrl.replay.validators import validate_replay


def test_same_seed_same_policies_replay_content_is_equivalent(tmp_path) -> None:
    replay_a_engine, replay_a = run_bot_match(
        team0_policy_id="aggressive",
        team1_policy_id="defensive",
        seed=42,
        max_ticks=120,
        output_root=tmp_path / "a",
    )
    replay_b_engine, replay_b = run_bot_match(
        team0_policy_id="aggressive",
        team1_policy_id="defensive",
        seed=42,
        max_ticks=120,
        output_root=tmp_path / "b",
    )

    assert replay_a_engine.state.model_dump(mode="json") == replay_b_engine.state.model_dump(
        mode="json"
    )
    assert replay_a is not None
    assert replay_b is not None
    metadata_a = json.loads((replay_a / "metadata.json").read_text(encoding="utf-8"))
    metadata_b = json.loads((replay_b / "metadata.json").read_text(encoding="utf-8"))
    metadata_a.pop("created_at_utc")
    metadata_b.pop("created_at_utc")

    assert metadata_a == metadata_b
    assert (replay_a / "frames.jsonl").read_text(encoding="utf-8") == (
        replay_b / "frames.jsonl"
    ).read_text(encoding="utf-8")
    assert (replay_a / "events.jsonl").read_text(encoding="utf-8") == (
        replay_b / "events.jsonl"
    ).read_text(encoding="utf-8")
    assert (replay_a / "summary.json").read_text(encoding="utf-8") == (
        replay_b / "summary.json"
    ).read_text(encoding="utf-8")


def test_saved_bot_replay_validates(tmp_path) -> None:
    _engine, replay_path = run_bot_match(
        team0_policy_id="kiter",
        team1_policy_id="aggressive",
        seed=42,
        max_ticks=120,
        output_root=tmp_path,
    )

    assert replay_path is not None
    validate_replay(replay_path)
