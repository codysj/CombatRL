"""Simple baseline policy registry."""

from combatrl.agents.aggressive_bot import AggressiveBot
from combatrl.agents.base import AgentPolicy
from combatrl.agents.defensive_bot import DefensiveBot
from combatrl.agents.kiter_bot import KiterBot
from combatrl.agents.protector_bot import ProtectorBot
from combatrl.agents.random_bot import RandomBot


def create_policy(policy_id: str, seed: int | None = None) -> AgentPolicy:
    """Create a supported heuristic baseline policy."""
    normalized_policy_id = policy_id.strip().lower()
    if normalized_policy_id == "random":
        return RandomBot(seed=seed)
    if normalized_policy_id == "aggressive":
        return AggressiveBot()
    if normalized_policy_id == "defensive":
        return DefensiveBot()
    if normalized_policy_id == "kiter":
        return KiterBot()
    if normalized_policy_id == "protector":
        return ProtectorBot()
    supported = "random, aggressive, defensive, kiter, protector"
    msg = f"unsupported policy_id {policy_id!r}; supported policies: {supported}"
    raise ValueError(msg)
