import pytest
from tests.replay_helpers import run_scripted_replay

from combatrl.renderer.camera import ReplayCamera


def test_coordinate_transform_uses_bottom_left_origin() -> None:
    camera = ReplayCamera(
        screen_width=200,
        screen_height=100,
        arena_width=100.0,
        arena_height=50.0,
        margin=0,
    )

    assert camera.sim_to_screen((0.0, 0.0)) == (0, 100)
    assert camera.sim_to_screen((100.0, 50.0)) == (200, 0)


def test_renderer_can_load_replay_in_headless_smoke_mode(tmp_path) -> None:
    pytest.importorskip("pygame")
    from combatrl.renderer.pygame_renderer import render_replay

    replay_path, _engine = run_scripted_replay(tmp_path)

    render_replay(str(replay_path), headless_smoke=True)
