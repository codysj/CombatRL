"""Defensive baseline policy."""

from combatrl.agents.utility import (
    choose_retreat_from_nearest_enemy,
    direction_action_toward,
    distance_between_agents,
    get_nearest_ally,
    get_nearest_enemy,
    is_attack_ready,
    is_enemy_in_attack_range,
    no_op,
)
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.match_state import MatchState


class DefensiveBot:
    """Retreats under pressure and only attacks from safer positions."""

    policy_id = "defensive"

    def __init__(
        self,
        low_hp_threshold: float = 0.40,
        ally_isolation_distance: float = 16.0,
    ) -> None:
        self.low_hp_threshold = low_hp_threshold
        self.ally_isolation_distance = ally_isolation_distance

    def reset(self, seed: int | None = None) -> None:
        _ = seed

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        agent = state.agents.get(agent_id)
        if agent is None or not agent.alive:
            return no_op(agent_id)

        enemy = get_nearest_enemy(state, agent_id)
        if enemy is None:
            ally = get_nearest_ally(state, agent_id)
            if ally is None:
                return no_op(agent_id)
            return ActionCommand(
                agent_id=agent_id,
                action_type=direction_action_toward(agent.position, ally.position),
            )

        hp_ratio = agent.hp / agent.max_hp
        enemy_distance = distance_between_agents(state, agent_id, enemy.agent_id)
        too_close_distance = max(2.0, agent.attack_range * 0.60)
        if hp_ratio < self.low_hp_threshold or enemy_distance < too_close_distance:
            return choose_retreat_from_nearest_enemy(state, agent_id)

        if is_attack_ready(state, agent_id) and is_enemy_in_attack_range(
            state, agent_id, enemy.agent_id
        ):
            return ActionCommand(agent_id=agent_id, action_type=ActionType.ATTACK_NEAREST)

        ally = get_nearest_ally(state, agent_id)
        if ally is not None and distance_between_agents(state, agent_id, ally.agent_id) > (
            self.ally_isolation_distance
        ):
            return ActionCommand(
                agent_id=agent_id,
                action_type=direction_action_toward(agent.position, ally.position),
            )

        return no_op(agent_id)
