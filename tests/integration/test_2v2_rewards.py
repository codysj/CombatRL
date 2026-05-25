from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.envs.reward_builder import RewardBuilder

CONTROLLED_AGENT_ID = "team0_ranged_dps_0"


def test_2v2_controlled_team_win_gives_positive_terminal_reward() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    for agent_id, agent in current.agents.items():
        if agent.team_id == 1:
            eliminate(current.agents[agent_id])
    current.terminal = True
    current.terminal_reason = "elimination"
    current.winner_team_id = 0

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.total_reward > 0.0
    assert reward.components["win_bonus"] == 1.0


def test_2v2_controlled_team_loss_gives_negative_terminal_reward() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    for agent_id, agent in current.agents.items():
        if agent.team_id == 0:
            eliminate(current.agents[agent_id])
    current.terminal = True
    current.terminal_reason = "elimination"
    current.winner_team_id = 1

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.total_reward < 0.0
    assert reward.components["loss_penalty"] == -1.0


def test_2v2_ally_and_controlled_death_penalties_can_apply_together() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    eliminate(current.agents["team0_tank_0"])
    eliminate(current.agents[CONTROLLED_AGENT_ID])

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.components["ally_death_penalty"] == -0.25
    assert reward.components["death_penalty"] == -0.5
