"""Profile-aware utility scoring and action reranking."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from combatrl.agents.utility import (
    direction_action_toward,
    get_candidate_actions,
    get_live_allies,
    get_live_enemies,
    get_lowest_hp_enemy,
    get_nearest_ally,
    get_nearest_enemy,
    no_op,
)
from combatrl.core.geometry import distance, normalize_vector
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.profiles import BehaviorProfile

ACTION_ORDER: tuple[ActionType, ...] = (
    ActionType.NO_OP,
    ActionType.MOVE_UP,
    ActionType.MOVE_DOWN,
    ActionType.MOVE_LEFT,
    ActionType.MOVE_RIGHT,
    ActionType.MOVE_UP_LEFT,
    ActionType.MOVE_UP_RIGHT,
    ActionType.MOVE_DOWN_LEFT,
    ActionType.MOVE_DOWN_RIGHT,
    ActionType.ATTACK_NEAREST,
)

ACTION_ORDER_INDEX = {action_type: index for index, action_type in enumerate(ACTION_ORDER)}

MOVEMENT_VECTORS: dict[ActionType, tuple[float, float]] = {
    ActionType.MOVE_UP: (0.0, -1.0),
    ActionType.MOVE_DOWN: (0.0, 1.0),
    ActionType.MOVE_LEFT: (-1.0, 0.0),
    ActionType.MOVE_RIGHT: (1.0, 0.0),
    ActionType.MOVE_UP_LEFT: (-1.0, -1.0),
    ActionType.MOVE_UP_RIGHT: (1.0, -1.0),
    ActionType.MOVE_DOWN_LEFT: (-1.0, 1.0),
    ActionType.MOVE_DOWN_RIGHT: (1.0, 1.0),
}


@dataclass(frozen=True)
class ProfileScoreDetail:
    """Debug detail for one candidate action."""

    action_type: ActionType
    base_score: float
    profile_score: float
    total_score: float


def score_action_with_profile(
    action: ActionCommand,
    state: MatchState,
    agent_id: str,
    profile: BehaviorProfile,
) -> float:
    """Return an inspectable profile utility delta for one valid candidate action."""
    agent = state.agents.get(agent_id)
    if agent is None or not agent.alive:
        return 0.0 if action.action_type == ActionType.NO_OP else -10.0

    nearest_enemy = get_nearest_enemy(state, agent_id)
    nearest_ally = get_nearest_ally(state, agent_id)
    threatened_ally = _select_threatened_ally(state, agent_id)
    threat_to_ally = (
        _nearest_enemy_to_agent(state, threatened_ally) if threatened_ally is not None else None
    )

    if nearest_enemy is None:
        return _score_no_enemy_action(action, agent, nearest_ally, profile)

    enemy_distance = distance(agent.position, nearest_enemy.position)
    hp_ratio = agent.hp / agent.max_hp
    low_hp_pressure = max(0.0, (0.55 - hp_ratio) / 0.55)
    close_pressure = _closeness(enemy_distance, max(1.0, agent.attack_range * 0.65))
    target_weakness = 1.0 - (nearest_enemy.hp / nearest_enemy.max_hp)

    if action.action_type == ActionType.ATTACK_NEAREST:
        return _score_attack_action(
            state=state,
            agent=agent,
            nearest_enemy=nearest_enemy,
            enemy_distance=enemy_distance,
            target_weakness=target_weakness,
            close_pressure=close_pressure,
            low_hp_pressure=low_hp_pressure,
            profile=profile,
        )

    if action.action_type == ActionType.NO_OP:
        hold_score = 0.08 * profile.caution * low_hp_pressure
        hold_score -= 0.18 * profile.aggression * (1.0 - target_weakness)
        return hold_score

    movement = _movement_vector(action.action_type)
    if movement == (0.0, 0.0):
        return 0.0

    score = 0.0
    toward_enemy = _direction_alignment(agent.position, nearest_enemy.position, movement)
    away_enemy = -toward_enemy
    score += 0.55 * profile.aggression * max(0.0, toward_enemy)
    score += 0.35 * profile.greed * target_weakness * max(0.0, toward_enemy)
    score += 0.75 * profile.caution * max(close_pressure, low_hp_pressure) * max(0.0, away_enemy)
    score += 0.65 * profile.spacing * close_pressure * max(0.0, away_enemy)

    lowest_hp_enemy = get_lowest_hp_enemy(state, agent_id)
    if lowest_hp_enemy is not None and lowest_hp_enemy.agent_id != nearest_enemy.agent_id:
        toward_low_hp = _direction_alignment(agent.position, lowest_hp_enemy.position, movement)
        score += 0.30 * profile.greed * _weakness(lowest_hp_enemy) * max(0.0, toward_low_hp)

    if nearest_ally is not None:
        ally_distance = distance(agent.position, nearest_ally.position)
        far_from_ally = min(1.0, ally_distance / max(agent.attack_range, 1.0))
        toward_ally = _direction_alignment(agent.position, nearest_ally.position, movement)
        score += 0.55 * profile.cohesion * far_from_ally * max(0.0, toward_ally)
        score -= 0.25 * profile.cohesion * far_from_ally * max(0.0, -toward_ally)

    if threatened_ally is not None:
        ally_threat_level = _ally_threat_level(state, threatened_ally)
        toward_threatened_ally = _direction_alignment(
            agent.position,
            threatened_ally.position,
            movement,
        )
        score += (
            0.70 * profile.protectiveness * ally_threat_level * max(0.0, toward_threatened_ally)
        )
        if threat_to_ally is not None:
            toward_ally_threat = _direction_alignment(
                agent.position, threat_to_ally.position, movement
            )
            score += (
                0.35 * profile.protectiveness * ally_threat_level * max(0.0, toward_ally_threat)
            )

    if agent.role == "ranged_dps":
        ideal_distance = agent.attack_range * 0.80
        if enemy_distance < ideal_distance:
            score += 0.30 * profile.spacing * max(0.0, away_enemy)

    return score


def rerank_actions(
    candidate_actions: list[ActionCommand],
    base_scores: list[float] | NDArray[np.floating],
    state: MatchState,
    agent_id: str,
    profile: BehaviorProfile,
) -> ActionCommand:
    """Choose the highest-scoring candidate after profile modulation."""
    agent = state.agents.get(agent_id)
    if agent is None or not agent.alive:
        return no_op(agent_id)
    if len(candidate_actions) != len(base_scores):
        msg = "candidate_actions and base_scores must have the same length"
        raise ValueError(msg)
    if not candidate_actions:
        return no_op(agent_id)

    details = score_candidates(candidate_actions, base_scores, state, agent_id, profile)
    best_index = min(
        range(len(details)),
        key=lambda index: (
            -details[index].total_score,
            ACTION_ORDER_INDEX[details[index].action_type],
        ),
    )
    return candidate_actions[best_index]


def score_candidates(
    candidate_actions: list[ActionCommand],
    base_scores: Sequence[float] | NDArray[np.floating],
    state: MatchState,
    agent_id: str,
    profile: BehaviorProfile,
) -> list[ProfileScoreDetail]:
    """Return debug score details for a candidate set."""
    details: list[ProfileScoreDetail] = []
    for action, raw_base_score in zip(candidate_actions, base_scores, strict=True):
        base_score = float(raw_base_score)
        profile_score = score_action_with_profile(action, state, agent_id, profile)
        details.append(
            ProfileScoreDetail(
                action_type=action.action_type,
                base_score=base_score,
                profile_score=profile_score,
                total_score=base_score + profile_score,
            )
        )
    return details


def _score_no_enemy_action(
    action: ActionCommand,
    agent: AgentState,
    nearest_ally: AgentState | None,
    profile: BehaviorProfile,
) -> float:
    if nearest_ally is None:
        return 0.0 if action.action_type == ActionType.NO_OP else -0.02
    if action.action_type == ActionType.NO_OP:
        return 0.02 * profile.caution
    if action.action_type == direction_action_toward(agent.position, nearest_ally.position):
        return 0.40 * profile.cohesion + 0.25 * profile.protectiveness
    return 0.0


def _score_attack_action(
    *,
    state: MatchState,
    agent: AgentState,
    nearest_enemy: AgentState,
    enemy_distance: float,
    target_weakness: float,
    close_pressure: float,
    low_hp_pressure: float,
    profile: BehaviorProfile,
) -> float:
    in_range = enemy_distance <= agent.attack_range
    attack_ready = agent.attack_cooldown_ticks == 0
    can_hit_now = in_range and attack_ready
    score = 0.18 * profile.aggression
    if can_hit_now:
        score += 0.90 * profile.aggression
        score += 0.45 * profile.greed * target_weakness
        score += 0.18 * profile.focus_fire * _shared_target_bonus(state, agent, nearest_enemy)
        score += 0.25 * profile.protectiveness * _enemy_threatens_ally(state, agent, nearest_enemy)
    else:
        score -= 0.28
    score -= 0.45 * profile.caution * max(close_pressure, low_hp_pressure)
    return score


def _select_threatened_ally(state: MatchState, agent_id: str) -> AgentState | None:
    allies = get_live_allies(state, agent_id)
    if not allies:
        return None
    return min(
        allies,
        key=lambda ally: (
            ally.hp / ally.max_hp,
            _nearest_enemy_distance(state, ally),
            ally.agent_id,
        ),
    )


def _nearest_enemy_to_agent(state: MatchState, agent: AgentState) -> AgentState | None:
    enemies = get_live_enemies(state, agent.agent_id)
    if not enemies:
        return None
    return min(
        enemies, key=lambda enemy: (distance(agent.position, enemy.position), enemy.agent_id)
    )


def _nearest_enemy_distance(state: MatchState, agent: AgentState) -> float:
    enemy = _nearest_enemy_to_agent(state, agent)
    if enemy is None:
        return float("inf")
    return distance(agent.position, enemy.position)


def _ally_threat_level(state: MatchState, ally: AgentState) -> float:
    nearest_enemy_distance = _nearest_enemy_distance(state, ally)
    hp_pressure = 1.0 - ally.hp / ally.max_hp
    proximity_pressure = _closeness(nearest_enemy_distance, max(ally.attack_range, 1.0))
    return max(hp_pressure, proximity_pressure)


def _enemy_threatens_ally(state: MatchState, agent: AgentState, enemy: AgentState) -> float:
    allies = [ally for ally in get_live_allies(state, agent.agent_id) if ally.alive]
    if not allies:
        return 0.0
    return max(
        _closeness(distance(enemy.position, ally.position), max(ally.attack_range, 1.0))
        for ally in allies
    )


def _shared_target_bonus(state: MatchState, agent: AgentState, enemy: AgentState) -> float:
    for ally in get_live_allies(state, agent.agent_id):
        if ally.current_target_id == enemy.agent_id:
            return 1.0
    return 0.0


def _movement_vector(action_type: ActionType) -> tuple[float, float]:
    raw_vector = MOVEMENT_VECTORS.get(action_type)
    if raw_vector is None:
        return (0.0, 0.0)
    return normalize_vector(raw_vector)


def _direction_alignment(
    source_position: tuple[float, float],
    target_position: tuple[float, float],
    movement_vector: tuple[float, float],
) -> float:
    target_vector = normalize_vector(
        (
            target_position[0] - source_position[0],
            target_position[1] - source_position[1],
        )
    )
    return movement_vector[0] * target_vector[0] + movement_vector[1] * target_vector[1]


def _closeness(actual_distance: float, threshold: float) -> float:
    if threshold <= 0.0:
        return 0.0
    return max(0.0, min(1.0, (threshold - actual_distance) / threshold))


def _weakness(agent: AgentState) -> float:
    return 1.0 - agent.hp / agent.max_hp


__all__ = [
    "ProfileScoreDetail",
    "get_candidate_actions",
    "rerank_actions",
    "score_action_with_profile",
    "score_candidates",
]
