from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.agents.kiter_bot import KiterBot
from combatrl.schemas.actions import ActionCommand, ActionType


def test_kiter_bot_returns_action_for_live_agent() -> None:
    action = KiterBot().select_action(make_state(), "team0_ranged_dps_0")

    assert isinstance(action, ActionCommand)


def test_kiter_bot_returns_no_op_for_dead_agent() -> None:
    state = make_state()
    eliminate(state.agents["team0_ranged_dps_0"])

    assert KiterBot().select_action(state, "team0_ranged_dps_0").action_type == ActionType.NO_OP


def test_kiter_bot_handles_no_live_enemies_without_crashing() -> None:
    state = make_state()
    eliminate(state.agents["team1_tank_0"])
    eliminate(state.agents["team1_ranged_dps_0"])

    assert KiterBot().select_action(state, "team0_ranged_dps_0").action_type == ActionType.NO_OP


def test_kiter_bot_moves_away_when_enemy_too_close() -> None:
    state = make_state()
    state.agents["team0_ranged_dps_0"].position = (20.0, 10.0)
    state.agents["team1_tank_0"].position = (25.0, 10.0)

    assert KiterBot().select_action(state, "team0_ranged_dps_0").action_type == ActionType.MOVE_LEFT


def test_kiter_bot_attacks_when_at_good_range_and_cooldown_ready() -> None:
    state = make_state()
    eliminate(state.agents["team1_ranged_dps_0"])
    state.agents["team0_ranged_dps_0"].position = (20.0, 10.0)
    state.agents["team1_tank_0"].position = (35.0, 10.0)

    assert (
        KiterBot().select_action(state, "team0_ranged_dps_0").action_type
        == ActionType.ATTACK_NEAREST
    )
