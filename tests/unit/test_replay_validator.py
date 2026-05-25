import json

import pytest
from tests.replay_helpers import run_scripted_replay

from combatrl.replay.validators import ReplayValidationError, validate_replay


def test_valid_replay_passes(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)

    validate_replay(replay_path)


def test_missing_metadata_fails(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)
    (replay_path / "metadata.json").unlink()

    with pytest.raises(ReplayValidationError, match="metadata.json"):
        validate_replay(replay_path)


def test_nonmonotonic_frames_fail(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)
    frames_path = replay_path / "frames.jsonl"
    lines = frames_path.read_text(encoding="utf-8").splitlines()
    second_frame = json.loads(lines[1])
    second_frame["tick"] = 0
    second_frame["sim_time_seconds"] = 0.0
    second_frame["events"] = []
    lines[1] = json.dumps(second_frame, sort_keys=True, separators=(",", ":"))
    frames_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ReplayValidationError, match="strictly increasing"):
        validate_replay(replay_path)


def test_event_with_unknown_agent_fails(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)
    events_path = replay_path / "events.jsonl"
    summary_path = replay_path / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["event_count"] += 1
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    events_path.write_text(
        events_path.read_text(encoding="utf-8")
        + json.dumps(
            {
                "event_id": "bad:tick-0:event-999",
                "tick": 0,
                "event_type": "agent_action_selected",
                "source_agent_id": "missing_agent",
                "target_agent_id": None,
                "payload": {},
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ReplayValidationError, match="unknown source"):
        validate_replay(replay_path)


def test_summary_final_frame_mismatch_fails(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)
    summary_path = replay_path / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["final_tick"] = summary["final_tick"] - 1
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ReplayValidationError, match="final frame tick"):
        validate_replay(replay_path)
