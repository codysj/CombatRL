"""Heuristic baseline agents for CombatRL."""

from combatrl.agents.aggressive_bot import AggressiveBot
from combatrl.agents.base import AgentPolicy
from combatrl.agents.defensive_bot import DefensiveBot
from combatrl.agents.kiter_bot import KiterBot
from combatrl.agents.protector_bot import ProtectorBot
from combatrl.agents.random_bot import RandomBot
from combatrl.agents.registry import create_policy

__all__ = [
    "AgentPolicy",
    "AggressiveBot",
    "DefensiveBot",
    "KiterBot",
    "ProtectorBot",
    "RandomBot",
    "create_policy",
]
