import numpy as np
from tests.unit.agent_test_helpers import make_state

from combatrl.profiles.loader import load_profile_by_id
from combatrl.profiles.modulation import (
    get_candidate_actions,
    rerank_actions,
    score_action_with_profile,
)
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.profiles import BehaviorProfile


def neutral_profile() -> BehaviorProfile:
    return BehaviorProfile(
        profile_id="neutral",
        aggression=0.0,
        caution=0.0,
        cohesion=0.0,
        protectiveness=0.0,
        focus_fire=0.0,
        greed=0.0,
        spacing=0.0,
        objective_bias=0.0,
    )


def test_aggressive_scores_attack_higher_than_defensive() -> None:
    state = make_state()
    agent = state.agents["team0_ranged_dps_0"]
    enemy = state.agents["team1_ranged_dps_0"]
    agent.position = (50.0, 30.0)
    enemy.position = (58.0, 30.0)
    enemy.hp = 20.0

    action = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.ATTACK_NEAREST)

    aggressive = score_action_with_profile(
        action, state, agent.agent_id, load_profile_by_id("aggressive")
    )
    defensive = score_action_with_profile(
        action, state, agent.agent_id, load_profile_by_id("defensive")
    )

    assert aggressive > defensive


def test_defensive_scores_retreat_higher_when_low_hp_and_enemy_close() -> None:
    state = make_state()
    agent = state.agents["team0_ranged_dps_0"]
    enemy = state.agents["team1_ranged_dps_0"]
    agent.position = (50.0, 30.0)
    agent.hp = 20.0
    enemy.position = (54.0, 30.0)
    defensive = load_profile_by_id("defensive")

    retreat = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_LEFT)
    attack = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.ATTACK_NEAREST)

    assert score_action_with_profile(
        retreat, state, agent.agent_id, defensive
    ) > score_action_with_profile(
        attack,
        state,
        agent.agent_id,
        defensive,
    )


def test_cohesion_scores_move_toward_ally_when_far() -> None:
    state = make_state()
    agent = state.agents["team0_ranged_dps_0"]
    ally = state.agents["team0_tank_0"]
    agent.position = (80.0, 30.0)
    ally.position = (20.0, 30.0)
    profile = load_profile_by_id("protective")

    toward_ally = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_LEFT)
    away_from_ally = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_RIGHT)

    assert score_action_with_profile(
        toward_ally,
        state,
        agent.agent_id,
        profile,
    ) > score_action_with_profile(away_from_ally, state, agent.agent_id, profile)


def test_protective_scores_protecting_threatened_ally() -> None:
    state = make_state()
    agent = state.agents["team0_ranged_dps_0"]
    ally = state.agents["team0_tank_0"]
    enemy = state.agents["team1_tank_0"]
    agent.position = (70.0, 30.0)
    ally.position = (40.0, 30.0)
    ally.hp = 40.0
    enemy.position = (43.0, 30.0)
    profile = load_profile_by_id("protective")

    toward_ally = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_LEFT)
    away_from_ally = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_RIGHT)

    assert score_action_with_profile(
        toward_ally,
        state,
        agent.agent_id,
        profile,
    ) > score_action_with_profile(away_from_ally, state, agent.agent_id, profile)


def test_kiter_scores_move_away_when_enemy_too_close() -> None:
    state = make_state()
    agent = state.agents["team0_ranged_dps_0"]
    enemy = state.agents["team1_ranged_dps_0"]
    agent.position = (50.0, 30.0)
    enemy.position = (53.0, 30.0)
    profile = load_profile_by_id("kiter")

    away = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_LEFT)
    toward = ActionCommand(agent_id=agent.agent_id, action_type=ActionType.MOVE_RIGHT)

    assert score_action_with_profile(
        away, state, agent.agent_id, profile
    ) > score_action_with_profile(
        toward,
        state,
        agent.agent_id,
        profile,
    )


def test_tied_scores_resolve_deterministically() -> None:
    state = make_state()
    agent_id = "team0_ranged_dps_0"
    candidates = get_candidate_actions(state, agent_id)
    scores = np.zeros(len(candidates), dtype=np.float64)

    selected = rerank_actions(candidates, scores, state, agent_id, neutral_profile())

    assert selected.action_type == ActionType.NO_OP
