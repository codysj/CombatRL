import argparse
from pathlib import Path

from scripts.run_2v2_env_episode import run_episode

from combatrl.replay.reader import ReplayReader
from combatrl.replay.validators import validate_replay


def test_2v2_env_episode_saves_valid_replay_matching_final_info(tmp_path: Path) -> None:
    summary = run_episode(
        argparse.Namespace(
            env_config=Path("configs/env/gym_2v2_controlled_ranged.yaml"),
            seed=42,
            policy="random",
            checkpoint=None,
            save_replay=True,
            replay_dir=tmp_path,
            max_env_steps=None,
            scripted_policy_id="aggressive",
        )
    )

    replay_path = Path(summary["replay_path"])
    assert replay_path.exists()
    validate_replay(replay_path)

    replay_summary = ReplayReader(replay_path).load_summary()
    assert replay_summary.final_tick == summary["final_tick"]
    assert replay_summary.winner_team_id == summary["winner_team_id"]
    assert replay_summary.team0_alive + replay_summary.team1_alive >= 0
