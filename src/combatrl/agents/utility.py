"""Shared deterministic helper functions for baseline agents."""

from combatrl.core.geometry import distance
from combatrl.core.types import Position2D
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.match_state import MatchState

MOVEMENT_ACTIONS: tuple[ActionType, ...] = (
    ActionType.MOVE_UP,
    ActionType.MOVE_DOWN,
    ActionType.MOVE_LEFT,
    ActionType.MOVE_RIGHT,
    ActionType.MOVE_UP_LEFT,
    ActionType.MOVE_UP_RIGHT,
    ActionType.MOVE_DOWN_LEFT,
    ActionType.MOVE_DOWN_RIGHT,
)


def no_op(agent_id: str) -> ActionCommand:
    """Build a no-op command for an agent."""
    return ActionCommand(agent_id=agent_id, action_type=ActionType.NO_OP)


def get_candidate_actions(state: MatchState, agent_id: str) -> list[ActionCommand]:
    """Return the small MVP candidate action set for profile reranking."""
    agent = state.agents.get(agent_id)
    if agent is None or not agent.alive:
        return [no_op(agent_id)]

    candidates = [ActionCommand(agent_id=agent_id, action_type=ActionType.NO_OP)]
    candidates.extend(
        ActionCommand(agent_id=agent_id, action_type=action_type)
        for action_type in MOVEMENT_ACTIONS
    )
    if get_live_enemies(state, agent_id):
        candidates.append(ActionCommand(agent_id=agent_id, action_type=ActionType.ATTACK_NEAREST))
    return candidates


def get_live_agents(state: MatchState) -> list[AgentState]:
    """Return live agents sorted by stable ID."""
    return [
        state.agents[agent_id] for agent_id in sorted(state.agents) if state.agents[agent_id].alive
    ]


def get_live_allies(state: MatchState, agent_id: str) -> list[AgentState]:
    """Return live allies excluding the selected agent, sorted by stable ID."""
    agent = state.agents.get(agent_id)
    if agent is None:
        return []
    return [
        state.agents[candidate_id]
        for candidate_id in sorted(state.agents)
        if candidate_id != agent_id
        and state.agents[candidate_id].alive
        and state.agents[candidate_id].team_id == agent.team_id
    ]


def get_live_enemies(state: MatchState, agent_id: str) -> list[AgentState]:
    """Return live enemies sorted by stable ID."""
    agent = state.agents.get(agent_id)
    if agent is None:
        return []
    return [
        state.agents[candidate_id]
        for candidate_id in sorted(state.agents)
        if state.agents[candidate_id].alive and state.agents[candidate_id].team_id != agent.team_id
    ]


def distance_between_agents(state: MatchState, a_id: str, b_id: str) -> float:
    """Return distance between two agents."""
    return distance(state.agents[a_id].position, state.agents[b_id].position)


def get_nearest_enemy(state: MatchState, agent_id: str) -> AgentState | None:
    """Return nearest live enemy, tie-breaking by agent ID."""
    agent = state.agents.get(agent_id)
    if agent is None or not agent.alive:
        return None
    enemies = get_live_enemies(state, agent_id)
    if not enemies:
        return None
    return min(
        enemies, key=lambda enemy: (distance(agent.position, enemy.position), enemy.agent_id)
    )


def get_lowest_hp_enemy(state: MatchState, agent_id: str) -> AgentState | None:
    """Return lowest-HP live enemy, tie-breaking by agent ID."""
    enemies = get_live_enemies(state, agent_id)
    if not enemies:
        return None
    return min(enemies, key=lambda enemy: (enemy.hp, enemy.agent_id))


def get_nearest_ally(state: MatchState, agent_id: str) -> AgentState | None:
    """Return nearest live ally, tie-breaking by agent ID."""
    agent = state.agents.get(agent_id)
    if agent is None or not agent.alive:
        return None
    allies = get_live_allies(state, agent_id)
    if not allies:
        return None
    return min(allies, key=lambda ally: (distance(agent.position, ally.position), ally.agent_id))


def get_lowest_hp_ally(state: MatchState, agent_id: str) -> AgentState | None:
    """Return lowest-HP live ally, tie-breaking by agent ID."""
    allies = get_live_allies(state, agent_id)
    if not allies:
        return None
    return min(allies, key=lambda ally: (ally.hp, ally.agent_id))


def is_enemy_in_attack_range(state: MatchState, agent_id: str, target_id: str) -> bool:
    """Return whether target is a live enemy inside the attacker's range."""
    agent = state.agents.get(agent_id)
    target = state.agents.get(target_id)
    if agent is None or target is None:
        return False
    return (
        agent.alive
        and target.alive
        and agent.team_id != target.team_id
        and distance(agent.position, target.position) <= agent.attack_range
    )


def is_attack_ready(state: MatchState, agent_id: str) -> bool:
    """Return whether an agent can attack this tick."""
    agent = state.agents.get(agent_id)
    return agent is not None and agent.alive and agent.attack_cooldown_ticks == 0


def direction_action_toward(source_pos: Position2D, target_pos: Position2D) -> ActionType:
    """Return the discrete movement action moving from source toward target."""
    dx = target_pos[0] - source_pos[0]
    dy = target_pos[1] - source_pos[1]
    horizontal = _horizontal_action(dx)
    vertical = _vertical_action(dy)
    return _combine_directions(vertical, horizontal)


def direction_action_away(source_pos: Position2D, target_pos: Position2D) -> ActionType:
    """Return the discrete movement action moving from source away from target."""
    return direction_action_toward(target_pos, source_pos)


def choose_attack_or_move_toward_target(
    state: MatchState,
    agent_id: str,
    target_id: str,
) -> ActionCommand:
    """Attack a target when ready and in range; otherwise move toward it."""
    agent = state.agents.get(agent_id)
    target = state.agents.get(target_id)
    if agent is None or target is None or not agent.alive or not target.alive:
        return no_op(agent_id)
    if is_attack_ready(state, agent_id) and is_enemy_in_attack_range(state, agent_id, target_id):
        return ActionCommand(agent_id=agent_id, action_type=ActionType.ATTACK_NEAREST)
    return ActionCommand(
        agent_id=agent_id,
        action_type=direction_action_toward(agent.position, target.position),
    )


def choose_retreat_from_nearest_enemy(state: MatchState, agent_id: str) -> ActionCommand:
    """Move away from nearest live enemy, or no-op when none exists."""
    agent = state.agents.get(agent_id)
    target = get_nearest_enemy(state, agent_id)
    if agent is None or not agent.alive or target is None:
        return no_op(agent_id)
    return ActionCommand(
        agent_id=agent_id,
        action_type=direction_action_away(agent.position, target.position),
    )


def _horizontal_action(dx: float) -> ActionType | None:
    if dx > 0.0:
        return ActionType.MOVE_RIGHT
    if dx < 0.0:
        return ActionType.MOVE_LEFT
    return None


def _vertical_action(dy: float) -> ActionType | None:
    if dy > 0.0:
        return ActionType.MOVE_DOWN
    if dy < 0.0:
        return ActionType.MOVE_UP
    return None


def _combine_directions(
    vertical: ActionType | None,
    horizontal: ActionType | None,
) -> ActionType:
    if vertical == ActionType.MOVE_UP and horizontal == ActionType.MOVE_LEFT:
        return ActionType.MOVE_UP_LEFT
    if vertical == ActionType.MOVE_UP and horizontal == ActionType.MOVE_RIGHT:
        return ActionType.MOVE_UP_RIGHT
    if vertical == ActionType.MOVE_DOWN and horizontal == ActionType.MOVE_LEFT:
        return ActionType.MOVE_DOWN_LEFT
    if vertical == ActionType.MOVE_DOWN and horizontal == ActionType.MOVE_RIGHT:
        return ActionType.MOVE_DOWN_RIGHT
    if vertical is not None:
        return vertical
    if horizontal is not None:
        return horizontal
    return ActionType.NO_OP
