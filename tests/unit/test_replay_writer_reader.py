from tests.replay_helpers import run_scripted_replay

from combatrl.replay.reader import ReplayReader


def test_writer_creates_replay_files(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)

    assert (replay_path / "metadata.json").exists()
    assert (replay_path / "frames.jsonl").exists()
    assert (replay_path / "events.jsonl").exists()
    assert (replay_path / "summary.json").exists()


def test_reader_loads_replay_components(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)
    reader = ReplayReader(replay_path)

    metadata = reader.load_metadata()
    frames = reader.load_frames()
    events = reader.load_events()
    summary = reader.load_summary()

    assert metadata.seed == 42
    assert frames[0].tick == 0
    assert len(events) == summary.event_count
    assert summary.frame_count == len(frames)


def test_reader_accepts_core_file_path(tmp_path) -> None:
    replay_path, _engine = run_scripted_replay(tmp_path)

    reader = ReplayReader(replay_path / "metadata.json")

    assert reader.load_metadata().match_id == "mvp_2v2_elimination_seed_42"
