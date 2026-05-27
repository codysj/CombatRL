"""Heuristic baseline agents for CombatRL."""

from combatrl.agents.aggressive_bot import AggressiveBot
from combatrl.agents.base import AgentPolicy
from combatrl.agents.defensive_bot import DefensiveBot
from combatrl.agents.kiter_bot import KiterBot
from combatrl.agents.protector_bot import ProtectorBot
from combatrl.agents.random_bot import RandomBot


def create_policy(policy_id: str, seed: int | None = None) -> AgentPolicy:
    """Create a supported policy without importing the registry at package import time."""
    from combatrl.agents.registry import create_policy as registry_create_policy

    return registry_create_policy(policy_id, seed=seed)


__all__ = [
    "AgentPolicy",
    "AggressiveBot",
    "DefensiveBot",
    "KiterBot",
    "ProtectorBot",
    "RandomBot",
    "create_policy",
]
