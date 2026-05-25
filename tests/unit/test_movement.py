import pytest

from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.configs import load_simulation_config
from combatrl.sim.engine import SimulationEngine


def make_engine() -> SimulationEngine:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    return SimulationEngine(config=config, seed=42)


def test_moving_up_changes_y_correctly() -> None:
    engine = make_engine()
    agent = engine.state.agents["team0_tank_0"]
    start_y = agent.position[1]

    engine.step([ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_UP)])

    assert agent.position[1] == pytest.approx(start_y - agent.movement_speed / 20.0)
    assert agent.position[0] == pytest.approx(15.0)


def test_diagonal_movement_is_normalized() -> None:
    engine = make_engine()
    agent = engine.state.agents["team0_tank_0"]
    start_x, start_y = agent.position

    engine.step([ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_UP_RIGHT)])

    expected_delta = (agent.movement_speed / 20.0) / (2.0**0.5)
    assert agent.position[0] == pytest.approx(start_x + expected_delta)
    assert agent.position[1] == pytest.approx(start_y - expected_delta)


def test_arena_clamping_works() -> None:
    engine = make_engine()
    agent = engine.state.agents["team0_tank_0"]
    agent.position = (0.0, 0.0)

    engine.step([ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_UP_LEFT)])

    assert agent.position == (0.0, 0.0)


def test_dead_agents_do_not_move() -> None:
    engine = make_engine()
    agent = engine.state.agents["team0_tank_0"]
    agent.hp = 0.0
    agent.alive = False
    start_position = agent.position

    engine.step([ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_RIGHT)])

    assert agent.position == start_position


def test_same_seed_and_actions_produce_same_positions() -> None:
    engine_a = make_engine()
    engine_b = make_engine()
    actions = [ActionCommand(agent_id="team0_tank_0", action_type=ActionType.MOVE_DOWN_RIGHT)]

    for _ in range(10):
        engine_a.step(actions)
        engine_b.step(actions)

    assert engine_a.state.model_dump(mode="json") == engine_b.state.model_dump(mode="json")
