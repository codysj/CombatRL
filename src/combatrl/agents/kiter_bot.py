"""Kiting baseline policy."""

from combatrl.agents.utility import (
    choose_attack_or_move_toward_target,
    direction_action_away,
    direction_action_toward,
    distance_between_agents,
    get_nearest_enemy,
    is_attack_ready,
    is_enemy_in_attack_range,
    no_op,
)
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.match_state import MatchState


class KiterBot:
    """Maintains spacing near attack range and attacks when ready."""

    policy_id = "kiter"

    def reset(self, seed: int | None = None) -> None:
        _ = seed

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        agent = state.agents.get(agent_id)
        if agent is None or not agent.alive:
            return no_op(agent_id)

        enemy = get_nearest_enemy(state, agent_id)
        if enemy is None:
            return no_op(agent_id)

        enemy_distance = distance_between_agents(state, agent_id, enemy.agent_id)
        too_close = max(1.0, agent.attack_range * 0.45)
        too_far = agent.attack_range * 0.95
        if enemy_distance < too_close:
            return ActionCommand(
                agent_id=agent_id,
                action_type=direction_action_away(agent.position, enemy.position),
            )
        if enemy_distance > too_far:
            return choose_attack_or_move_toward_target(state, agent_id, enemy.agent_id)
        if is_attack_ready(state, agent_id) and is_enemy_in_attack_range(
            state, agent_id, enemy.agent_id
        ):
            return ActionCommand(agent_id=agent_id, action_type=ActionType.ATTACK_NEAREST)

        return ActionCommand(
            agent_id=agent_id,
            action_type=_deterministic_strafe(state.tick, agent_id, agent.position, enemy.position),
        )


def _deterministic_strafe(
    tick: int,
    agent_id: str,
    source_pos: tuple[float, float],
    target_pos: tuple[float, float],
) -> ActionType:
    toward = direction_action_toward(source_pos, target_pos)
    phase = (tick + sum(ord(char) for char in agent_id)) % 2
    if toward in {ActionType.MOVE_LEFT, ActionType.MOVE_RIGHT}:
        return ActionType.MOVE_UP if phase == 0 else ActionType.MOVE_DOWN
    if toward in {ActionType.MOVE_UP, ActionType.MOVE_DOWN}:
        return ActionType.MOVE_LEFT if phase == 0 else ActionType.MOVE_RIGHT
    if toward in {ActionType.MOVE_UP_LEFT, ActionType.MOVE_DOWN_RIGHT}:
        return ActionType.MOVE_UP_RIGHT if phase == 0 else ActionType.MOVE_DOWN_LEFT
    if toward in {ActionType.MOVE_UP_RIGHT, ActionType.MOVE_DOWN_LEFT}:
        return ActionType.MOVE_UP_LEFT if phase == 0 else ActionType.MOVE_DOWN_RIGHT
    return ActionType.NO_OP
