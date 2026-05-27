"""Simple baseline policy registry."""

from combatrl.agents.aggressive_bot import AggressiveBot
from combatrl.agents.base import AgentPolicy
from combatrl.agents.defensive_bot import DefensiveBot
from combatrl.agents.kiter_bot import KiterBot
from combatrl.agents.profiled_bot import ProfiledBot
from combatrl.agents.protector_bot import ProtectorBot
from combatrl.agents.random_bot import RandomBot
from combatrl.profiles.loader import load_profile_by_id


def create_policy(policy_id: str, seed: int | None = None) -> AgentPolicy:
    """Create a supported heuristic baseline policy."""
    normalized_policy_id = policy_id.strip().lower()
    if normalized_policy_id.startswith("profiled:"):
        return _create_profiled_policy(normalized_policy_id, seed=seed)
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
    supported = (
        "random, aggressive, defensive, kiter, protector, profiled:<profile>, "
        "profiled:<base_policy>:<profile>"
    )
    msg = f"unsupported policy_id {policy_id!r}; supported policies: {supported}"
    raise ValueError(msg)


def _create_profiled_policy(policy_id: str, seed: int | None) -> AgentPolicy:
    parts = policy_id.split(":")
    if len(parts) == 2:
        base_policy_id = "aggressive"
        profile_id = parts[1]
    elif len(parts) == 3:
        base_policy_id = parts[1]
        profile_id = parts[2]
    else:
        msg = (
            f"unsupported profiled policy syntax {policy_id!r}; use "
            "profiled:<profile> or profiled:<base_policy>:<profile>"
        )
        raise ValueError(msg)
    if base_policy_id == "profiled":
        msg = "profiled policies cannot wrap another profiled policy"
        raise ValueError(msg)
    base_policy = create_policy(base_policy_id, seed=seed)
    profile = load_profile_by_id(profile_id)
    return ProfiledBot(base_policy=base_policy, profile=profile)
