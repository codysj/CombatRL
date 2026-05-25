from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.agents.defensive_bot import DefensiveBot
from combatrl.schemas.actions import ActionCommand, ActionType


def test_defensive_bot_returns_action_for_live_agent() -> None:
    action = DefensiveBot().select_action(make_state(), "team0_tank_0")

    assert isinstance(action, ActionCommand)


def test_defensive_bot_returns_no_op_for_dead_agent() -> None:
    state = make_state()
    eliminate(state.agents["team0_tank_0"])

    assert DefensiveBot().select_action(state, "team0_tank_0").action_type == ActionType.NO_OP


def test_defensive_bot_handles_no_live_enemies_without_crashing() -> None:
    state = make_state()
    eliminate(state.agents["team1_tank_0"])
    eliminate(state.agents["team1_ranged_dps_0"])

    action = DefensiveBot().select_action(state, "team0_tank_0")

    assert isinstance(action, ActionCommand)


def test_defensive_bot_retreats_when_low_hp() -> None:
    state = make_state()
    state.agents["team0_tank_0"].position = (20.0, 10.0)
    state.agents["team0_tank_0"].hp = 50.0
    state.agents["team1_tank_0"].position = (25.0, 10.0)

    assert DefensiveBot().select_action(state, "team0_tank_0").action_type == ActionType.MOVE_LEFT


def test_defensive_bot_retreats_when_enemy_too_close() -> None:
    state = make_state()
    state.agents["team0_ranged_dps_0"].position = (20.0, 10.0)
    state.agents["team1_tank_0"].position = (24.0, 10.0)

    assert (
        DefensiveBot().select_action(state, "team0_ranged_dps_0").action_type
        == ActionType.MOVE_LEFT
    )
