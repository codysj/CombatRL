"""Discrete RL action codec for simulator commands."""

import numpy as np
from numpy.typing import NDArray

from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.match_state import MatchState

ACTION_ID_TO_TYPE: tuple[ActionType, ...] = (
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

ACTION_TYPE_TO_ID: dict[ActionType, int] = {
    action_type: action_id for action_id, action_type in enumerate(ACTION_ID_TO_TYPE)
}

MOVEMENT_ACTION_TYPES: frozenset[ActionType] = frozenset(
    {
        ActionType.MOVE_UP,
        ActionType.MOVE_DOWN,
        ActionType.MOVE_LEFT,
        ActionType.MOVE_RIGHT,
        ActionType.MOVE_UP_LEFT,
        ActionType.MOVE_UP_RIGHT,
        ActionType.MOVE_DOWN_LEFT,
        ActionType.MOVE_DOWN_RIGHT,
    }
)


class ActionCodec:
    """Map between Gymnasium discrete actions and simulator action commands."""

    def n_actions(self) -> int:
        """Return the size of the discrete RL action space."""
        return len(ACTION_ID_TO_TYPE)

    def decode(self, action_id: int, agent_id: str) -> ActionCommand:
        """Decode an integer action ID, falling back to no-op when invalid."""
        if 0 <= action_id < self.n_actions():
            action_type = ACTION_ID_TO_TYPE[action_id]
        else:
            action_type = ActionType.NO_OP
        return ActionCommand(agent_id=agent_id, action_type=action_type)

    def encode(self, action_type: ActionType) -> int:
        """Encode a simulator action type into its RL action ID."""
        return ACTION_TYPE_TO_ID[action_type]

    def valid_action_mask(self, state: MatchState, agent_id: str) -> NDArray[np.int8]:
        """Return an int8 mask where 1 means the action is valid."""
        mask = np.zeros(self.n_actions(), dtype=np.int8)
        mask[self.fallback_action_id()] = 1
        agent = state.agents.get(agent_id)
        if agent is None or not agent.alive:
            return mask

        for action_type in MOVEMENT_ACTION_TYPES:
            mask[self.encode(action_type)] = 1

        if any(enemy.alive and enemy.team_id != agent.team_id for enemy in state.agents.values()):
            mask[self.encode(ActionType.ATTACK_NEAREST)] = 1
        return mask

    def fallback_action_id(self) -> int:
        """Return the no-op fallback action ID."""
        return ACTION_TYPE_TO_ID[ActionType.NO_OP]

    def fallback_action(self, agent_id: str) -> ActionCommand:
        """Return a no-op fallback command for the supplied agent."""
        return self.decode(self.fallback_action_id(), agent_id)
