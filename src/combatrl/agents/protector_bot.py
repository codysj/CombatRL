"""Protector baseline policy."""

from combatrl.agents.utility import (
    choose_attack_or_move_toward_target,
    direction_action_toward,
    distance_between_agents,
    get_live_allies,
    get_live_enemies,
    get_lowest_hp_enemy,
    is_attack_ready,
    is_enemy_in_attack_range,
    no_op,
)
from combatrl.core.geometry import distance
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.match_state import MatchState


class ProtectorBot:
    """Stays near vulnerable allies and attacks threats close to them."""

    policy_id = "protector"

    def __init__(self, ally_follow_distance: float = 10.0) -> None:
        self.ally_follow_distance = ally_follow_distance

    def reset(self, seed: int | None = None) -> None:
        _ = seed

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        agent = state.agents.get(agent_id)
        if agent is None or not agent.alive:
            return no_op(agent_id)

        allies = get_live_allies(state, agent_id)
        if not allies:
            target = get_lowest_hp_enemy(state, agent_id)
            if target is None:
                return no_op(agent_id)
            return choose_attack_or_move_toward_target(state, agent_id, target.agent_id)

        threatened_ally = _select_threatened_ally(state, allies)
        threat = _nearest_enemy_to_agent(state, threatened_ally)
        if threat is None:
            return ActionCommand(
                agent_id=agent_id,
                action_type=direction_action_toward(agent.position, threatened_ally.position),
            )

        ally_distance = distance_between_agents(state, agent_id, threatened_ally.agent_id)
        if ally_distance > self.ally_follow_distance:
            return ActionCommand(
                agent_id=agent_id,
                action_type=direction_action_toward(agent.position, threatened_ally.position),
            )

        if is_attack_ready(state, agent_id) and is_enemy_in_attack_range(
            state, agent_id, threat.agent_id
        ):
            return ActionCommand(agent_id=agent_id, action_type=ActionType.ATTACK_NEAREST)

        threat_to_ally_distance = distance(threat.position, threatened_ally.position)
        guard_radius = max(threatened_ally.attack_range * 1.25, self.ally_follow_distance)
        if threat_to_ally_distance <= guard_radius:
            return ActionCommand(
                agent_id=agent_id,
                action_type=direction_action_toward(agent.position, threat.position),
            )

        return no_op(agent_id)


def _select_threatened_ally(state: MatchState, allies: list[AgentState]) -> AgentState:
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
