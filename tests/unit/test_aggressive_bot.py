from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.agents.aggressive_bot import AggressiveBot
from combatrl.schemas.actions import ActionCommand, ActionType


def test_aggressive_bot_returns_action_for_live_agent() -> None:
    action = AggressiveBot().select_action(make_state(), "team0_tank_0")

    assert isinstance(action, ActionCommand)


def test_aggressive_bot_returns_no_op_for_dead_agent() -> None:
    state = make_state()
    eliminate(state.agents["team0_tank_0"])

    assert AggressiveBot().select_action(state, "team0_tank_0").action_type == ActionType.NO_OP


def test_aggressive_bot_handles_no_live_enemies_without_crashing() -> None:
    state = make_state()
    eliminate(state.agents["team1_tank_0"])
    eliminate(state.agents["team1_ranged_dps_0"])

    assert AggressiveBot().select_action(state, "team0_tank_0").action_type == ActionType.NO_OP


def test_aggressive_bot_moves_toward_enemy_when_out_of_range() -> None:
    state = make_state()
    eliminate(state.agents["team1_ranged_dps_0"])
    state.agents["team0_tank_0"].position = (10.0, 10.0)
    state.agents["team1_tank_0"].position = (30.0, 10.0)

    assert AggressiveBot().select_action(state, "team0_tank_0").action_type == ActionType.MOVE_RIGHT


def test_aggressive_bot_attacks_when_in_range_and_cooldown_ready() -> None:
    state = make_state()
    eliminate(state.agents["team1_ranged_dps_0"])
    state.agents["team0_tank_0"].position = (10.0, 10.0)
    state.agents["team1_tank_0"].position = (15.0, 10.0)

    assert (
        AggressiveBot().select_action(state, "team0_tank_0").action_type
        == ActionType.ATTACK_NEAREST
    )
