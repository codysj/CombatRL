"""Agent policy interface for heuristic and future learned policies."""

from typing import Protocol

from combatrl.schemas.actions import ActionCommand
from combatrl.schemas.match_state import MatchState


class AgentPolicy(Protocol):
    """Minimal policy contract for selecting one simulator action."""

    policy_id: str

    def reset(self, seed: int | None = None) -> None:
        """Reset any deterministic policy-local state."""

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        """Select a public simulator action for one agent."""
