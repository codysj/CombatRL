"""Aggressive baseline policy."""

from combatrl.agents.utility import choose_attack_or_move_toward_target, get_lowest_hp_enemy, no_op
from combatrl.schemas.actions import ActionCommand
from combatrl.schemas.match_state import MatchState


class AggressiveBot:
    """Prioritizes low-HP enemies and closes distance to fight."""

    policy_id = "aggressive"

    def reset(self, seed: int | None = None) -> None:
        _ = seed

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        agent = state.agents.get(agent_id)
        if agent is None or not agent.alive:
            return no_op(agent_id)
        target = get_lowest_hp_enemy(state, agent_id)
        if target is None:
            return no_op(agent_id)
        return choose_attack_or_move_toward_target(state, agent_id, target.agent_id)
