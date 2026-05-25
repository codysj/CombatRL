"""Seeded random baseline policy."""

from combatrl.agents.utility import get_live_enemies, no_op
from combatrl.core.rng import ProjectRNG
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.match_state import MatchState

_MOVEMENT_ACTIONS: tuple[ActionType, ...] = (
    ActionType.MOVE_UP,
    ActionType.MOVE_DOWN,
    ActionType.MOVE_LEFT,
    ActionType.MOVE_RIGHT,
    ActionType.MOVE_UP_LEFT,
    ActionType.MOVE_UP_RIGHT,
    ActionType.MOVE_DOWN_LEFT,
    ActionType.MOVE_DOWN_RIGHT,
)


class RandomBot:
    """Uniformly samples simple valid action types from a seeded RNG."""

    policy_id = "random"

    def __init__(self, seed: int | None = None) -> None:
        self._seed = 0 if seed is None else seed
        self._rng = ProjectRNG(self._seed)

    def reset(self, seed: int | None = None) -> None:
        self._seed = self._seed if seed is None else seed
        self._rng = ProjectRNG(self._seed)

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        agent = state.agents.get(agent_id)
        if agent is None or not agent.alive:
            return no_op(agent_id)

        choices = [ActionType.NO_OP, *_MOVEMENT_ACTIONS]
        if get_live_enemies(state, agent_id):
            choices.append(ActionType.ATTACK_NEAREST)
        return ActionCommand(agent_id=agent_id, action_type=self._rng.choice(choices))
