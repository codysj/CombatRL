from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.agents.aggressive_bot import AggressiveBot
from combatrl.agents.base import AgentPolicy
from combatrl.agents.profiled_bot import ProfiledBot
from combatrl.profiles.loader import load_profile_by_id
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.match_state import MatchState


class FixedAttackPolicy:
    policy_id = "fixed_attack"

    def reset(self, seed: int | None = None) -> None:
        _ = seed

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        _ = state
        return ActionCommand(agent_id=agent_id, action_type=ActionType.ATTACK_NEAREST)


def test_profiled_bot_returns_valid_action_command() -> None:
    state = make_state()
    bot = ProfiledBot(AggressiveBot(), load_profile_by_id("aggressive"))

    action = bot.select_action(state, "team0_ranged_dps_0")

    assert isinstance(action, ActionCommand)
    assert action.agent_id == "team0_ranged_dps_0"


def test_profiled_bot_dead_agent_returns_no_op() -> None:
    state = make_state()
    eliminate(state.agents["team0_ranged_dps_0"])
    bot = ProfiledBot(AggressiveBot(), load_profile_by_id("aggressive"))

    action = bot.select_action(state, "team0_ranged_dps_0")

    assert action.action_type == ActionType.NO_OP


def test_profiled_bot_same_state_seed_profile_is_deterministic() -> None:
    state = make_state()
    bot_a = ProfiledBot(AggressiveBot(), load_profile_by_id("defensive"))
    bot_b = ProfiledBot(AggressiveBot(), load_profile_by_id("defensive"))
    bot_a.reset(123)
    bot_b.reset(123)

    assert bot_a.select_action(state, "team0_ranged_dps_0") == bot_b.select_action(
        state,
        "team0_ranged_dps_0",
    )


def test_different_profiles_can_choose_different_actions() -> None:
    state = make_state()
    agent = state.agents["team0_ranged_dps_0"]
    enemy = state.agents["team1_ranged_dps_0"]
    agent.position = (50.0, 30.0)
    agent.hp = 20.0
    enemy.position = (54.0, 30.0)

    aggressive = ProfiledBot(FixedAttackPolicy(), load_profile_by_id("aggressive"))
    defensive = ProfiledBot(FixedAttackPolicy(), load_profile_by_id("defensive"))

    assert (
        aggressive.select_action(state, agent.agent_id).action_type
        != defensive.select_action(
            state,
            agent.agent_id,
        ).action_type
    )


def test_base_policy_output_can_be_reranked_away_from() -> None:
    state = make_state()
    agent = state.agents["team0_ranged_dps_0"]
    enemy = state.agents["team1_ranged_dps_0"]
    agent.position = (50.0, 30.0)
    agent.hp = 15.0
    enemy.position = (54.0, 30.0)
    bot: AgentPolicy = ProfiledBot(FixedAttackPolicy(), load_profile_by_id("defensive"))

    action = bot.select_action(state, agent.agent_id)

    assert action.action_type != ActionType.ATTACK_NEAREST
