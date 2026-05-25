import json

from tests.replay_helpers import run_scripted_replay


def test_same_seed_produces_equivalent_replay_content(tmp_path) -> None:
    replay_a, _engine_a = run_scripted_replay(tmp_path / "a", seed=42)
    replay_b, _engine_b = run_scripted_replay(tmp_path / "b", seed=42)

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
