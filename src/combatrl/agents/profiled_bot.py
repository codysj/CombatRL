"""Profile-aware policy wrapper."""

import numpy as np

from combatrl.agents.base import AgentPolicy
from combatrl.agents.utility import get_candidate_actions, no_op
from combatrl.profiles.modulation import rerank_actions
from combatrl.schemas.actions import ActionCommand
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.profiles import BehaviorProfile


class ProfiledBot:
    """Wrap a base policy and rerank simple candidate actions with a profile."""

    def __init__(
        self,
        base_policy: AgentPolicy,
        profile: BehaviorProfile,
        candidate_limit: int | None = None,
        base_action_bonus: float = 0.05,
    ) -> None:
        self.base_policy = base_policy
        self.profile = profile
        self.profile_id = profile.profile_id
        self.candidate_limit = candidate_limit
        self.base_action_bonus = base_action_bonus
        self.policy_id = f"profiled:{base_policy.policy_id}:{profile.profile_id}"

    def reset(self, seed: int | None = None) -> None:
        self.base_policy.reset(seed)

    def select_action(self, state: MatchState, agent_id: str) -> ActionCommand:
        agent = state.agents.get(agent_id)
        if agent is None or not agent.alive:
            return no_op(agent_id)

        base_action = self.base_policy.select_action(state, agent_id)
        candidates = get_candidate_actions(state, agent_id)
        if self.candidate_limit is not None:
            candidates = candidates[: self.candidate_limit]
        if base_action.action_type not in {candidate.action_type for candidate in candidates}:
            candidates.append(base_action)

        base_scores = np.zeros(len(candidates), dtype=np.float64)
        for index, candidate in enumerate(candidates):
            if candidate.action_type == base_action.action_type:
                base_scores[index] = self.base_action_bonus
                break

        return rerank_actions(candidates, base_scores, state, agent_id, self.profile)
