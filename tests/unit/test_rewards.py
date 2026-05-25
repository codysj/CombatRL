import math

from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.envs.reward_builder import RewardBuilder
from combatrl.schemas.replay import make_event_log

CONTROLLED_AGENT_ID = "team0_ranged_dps_0"


def _damage_event(
    source_agent_id: str,
    target_agent_id: str,
    damage: float,
):
    return make_event_log(
        match_id="test_match",
        tick=1,
        index=0,
        event_type="agent_damaged",
        source_agent_id=source_agent_id,
        target_agent_id=target_agent_id,
        payload={"damage": damage},
    )


def test_damage_dealt_increases_reward() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)

    reward = RewardBuilder().compute(
        previous,
        current,
        [_damage_event(CONTROLLED_AGENT_ID, "team1_ranged_dps_0", 10.0)],
        CONTROLLED_AGENT_ID,
    )

    assert reward.components["damage_dealt"] > 0.0


def test_damage_taken_decreases_reward() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)

    reward = RewardBuilder().compute(
        previous,
        current,
        [_damage_event("team1_ranged_dps_0", CONTROLLED_AGENT_ID, 15.0)],
        CONTROLLED_AGENT_ID,
    )

    assert reward.components["damage_taken_penalty"] < 0.0


def test_win_terminal_reward_positive() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    current.terminal = True
    current.terminal_reason = "elimination"
    current.winner_team_id = 0

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.total_reward > 0.0


def test_loss_terminal_reward_negative() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    current.terminal = True
    current.terminal_reason = "elimination"
    current.winner_team_id = 1

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.total_reward < 0.0


def test_invalid_action_penalty_applied_once() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)

    reward = RewardBuilder().compute(
        previous,
        current,
        [],
        CONTROLLED_AGENT_ID,
        invalid_action=True,
    )

    assert reward.components["invalid_action_penalty"] == -0.02


def test_zero_event_step_produces_only_time_penalty() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.total_reward == -0.001
    assert reward.components["time_penalty"] == -0.001


def test_reward_breakdown_sums_exactly_to_total_reward() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)

    reward = RewardBuilder().compute(
        previous,
        current,
        [_damage_event(CONTROLLED_AGENT_ID, "team1_ranged_dps_0", 10.0)],
        CONTROLLED_AGENT_ID,
        invalid_action=True,
    )

    assert math.isclose(sum(reward.components.values()), reward.total_reward)


def test_ally_death_penalty_applies_for_controlled_ally_death() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    eliminate(current.agents["team0_tank_0"])

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.components["ally_death_penalty"] == -0.25


def test_controlled_agent_death_penalty_applies() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    eliminate(current.agents[CONTROLLED_AGENT_ID])

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.components["death_penalty"] == -0.5


def test_terminal_team_outcome_uses_controlled_team_not_agent_survival() -> None:
    previous = make_state()
    current = previous.model_copy(deep=True)
    eliminate(current.agents[CONTROLLED_AGENT_ID])
    current.terminal = True
    current.terminal_reason = "elimination"
    current.winner_team_id = 0

    reward = RewardBuilder().compute(previous, current, [], CONTROLLED_AGENT_ID)

    assert reward.components["win_bonus"] == 1.0
    assert reward.components["loss_penalty"] == 0.0
