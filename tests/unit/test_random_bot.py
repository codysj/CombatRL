from tests.unit.agent_test_helpers import eliminate, make_state, movement_actions

from combatrl.agents.random_bot import RandomBot
from combatrl.schemas.actions import ActionCommand, ActionType


def test_random_bot_returns_action_for_live_agent() -> None:
    state = make_state()
    action = RandomBot(seed=1).select_action(state, "team0_tank_0")

    assert isinstance(action, ActionCommand)
    assert action.agent_id == "team0_tank_0"


def test_random_bot_returns_no_op_for_dead_agent() -> None:
    state = make_state()
    eliminate(state.agents["team0_tank_0"])

    assert RandomBot(seed=1).select_action(state, "team0_tank_0").action_type == ActionType.NO_OP


def test_random_bot_handles_no_live_enemies_without_crashing() -> None:
    state = make_state()
    eliminate(state.agents["team1_tank_0"])
    eliminate(state.agents["team1_ranged_dps_0"])
    bot = RandomBot(seed=1)

    for _ in range(20):
        action = bot.select_action(state, "team0_tank_0")
        assert action.action_type in {ActionType.NO_OP, *movement_actions()}


def test_random_bot_sequence_is_deterministic_after_reset() -> None:
    state = make_state()
    bot_a = RandomBot(seed=7)
    bot_b = RandomBot(seed=99)
    bot_b.reset(7)

    sequence_a = [bot_a.select_action(state, "team0_tank_0").action_type for _ in range(10)]
    sequence_b = [bot_b.select_action(state, "team0_tank_0").action_type for _ in range(10)]

    assert sequence_a == sequence_b
