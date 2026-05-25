from tests.replay_helpers import run_scripted_replay

from combatrl.replay.reader import ReplayReader
from combatrl.replay.validators import validate_replay


def test_scripted_match_replay_roundtrip(tmp_path) -> None:
    replay_path, engine = run_scripted_replay(tmp_path)

    validate_replay(replay_path)
    reader = ReplayReader(replay_path)
    frames = reader.load_frames()
    events = reader.load_events()
    final_frame = frames[-1]

    assert final_frame.tick == engine.state.tick
    assert final_frame.scoreboard["terminal_reason"] == engine.state.terminal_reason
    assert final_frame.scoreboard["winner_team_id"] == engine.state.winner_team_id
    assert len(events) > 0
    assert any(event.event_type == "agent_attacked" for event in events)
