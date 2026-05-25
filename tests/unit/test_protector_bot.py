from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.agents.protector_bot import ProtectorBot
from combatrl.schemas.actions import ActionCommand, ActionType


def test_protector_bot_returns_action_for_live_agent() -> None:
    action = ProtectorBot().select_action(make_state(), "team0_tank_0")

    assert isinstance(action, ActionCommand)


def test_protector_bot_returns_no_op_for_dead_agent() -> None:
    state = make_state()
    eliminate(state.agents["team0_tank_0"])

    assert ProtectorBot().select_action(state, "team0_tank_0").action_type == ActionType.NO_OP


def test_protector_bot_handles_no_live_enemies_without_crashing() -> None:
    state = make_state()
    eliminate(state.agents["team1_tank_0"])
    eliminate(state.agents["team1_ranged_dps_0"])

    action = ProtectorBot().select_action(state, "team0_tank_0")

    assert isinstance(action, ActionCommand)


def test_protector_bot_moves_toward_threatened_ally() -> None:
    state = make_state()
    state.agents["team0_tank_0"].position = (10.0, 10.0)
    state.agents["team0_ranged_dps_0"].position = (30.0, 10.0)
    state.agents["team0_ranged_dps_0"].hp = 20.0
    state.agents["team1_tank_0"].position = (32.0, 10.0)

    assert ProtectorBot().select_action(state, "team0_tank_0").action_type == ActionType.MOVE_RIGHT


def test_protector_bot_targets_enemy_near_threatened_ally() -> None:
    state = make_state()
    state.agents["team0_tank_0"].position = (25.0, 10.0)
    state.agents["team0_ranged_dps_0"].position = (30.0, 10.0)
    state.agents["team0_ranged_dps_0"].hp = 20.0
    state.agents["team1_tank_0"].position = (32.0, 10.0)
    eliminate(state.agents["team1_ranged_dps_0"])

    assert (
        ProtectorBot().select_action(state, "team0_tank_0").action_type == ActionType.ATTACK_NEAREST
    )
