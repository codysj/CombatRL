"""Runtime invariant checks for simulator state."""

import math

from combatrl.schemas.match_state import MatchState


class InvariantViolation(Exception):  # noqa: N818
    """Raised when authoritative simulator state violates an invariant."""


def validate_match_state(state: MatchState) -> None:
    """Validate runtime invariants that must hold for every simulator tick."""
    if state.tick < 0 or state.tick > state.max_ticks:
        msg = f"tick must be in [0, {state.max_ticks}], got {state.tick}"
        raise InvariantViolation(msg)

    if state.terminal and state.terminal_reason is None:
        msg = "terminal state requires terminal_reason"
        raise InvariantViolation(msg)

    if state.terminal_reason == "timeout" and state.winner_team_id is not None:
        msg = "timeout terminal states must not have a winner in P1"
        raise InvariantViolation(msg)

    agent_ids = set(state.agents)
    for key, agent in state.agents.items():
        if key != agent.agent_id:
            msg = f"agents key {key!r} does not match agent_id {agent.agent_id!r}"
            raise InvariantViolation(msg)

        x, y = agent.position
        if not math.isfinite(x) or not math.isfinite(y):
            msg = f"agent {agent.agent_id} position must be finite"
            raise InvariantViolation(msg)

        vx, vy = agent.velocity
        if not math.isfinite(vx) or not math.isfinite(vy):
            msg = f"agent {agent.agent_id} velocity must be finite"
            raise InvariantViolation(msg)

        if x < 0.0 or x > state.arena_width or y < 0.0 or y > state.arena_height:
            msg = f"agent {agent.agent_id} position is outside the arena"
            raise InvariantViolation(msg)

        if not math.isfinite(agent.hp) or not math.isfinite(agent.max_hp):
            msg = f"agent {agent.agent_id} hp values must be finite"
            raise InvariantViolation(msg)

        if agent.max_hp <= 0.0 or agent.hp < 0.0 or agent.hp > agent.max_hp:
            msg = f"agent {agent.agent_id} hp must be in [0, max_hp]"
            raise InvariantViolation(msg)

        if agent.attack_cooldown_ticks < 0 or agent.ability_cooldown_ticks < 0:
            msg = f"agent {agent.agent_id} cooldowns must be non-negative"
            raise InvariantViolation(msg)

        if agent.alive != (agent.hp > 0.0):
            msg = f"agent {agent.agent_id} alive must equal hp > 0"
            raise InvariantViolation(msg)

        if agent.current_target_id is not None and agent.current_target_id not in agent_ids:
            msg = f"agent {agent.agent_id} target {agent.current_target_id!r} does not exist"
            raise InvariantViolation(msg)
