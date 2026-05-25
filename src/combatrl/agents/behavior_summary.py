"""Lightweight behavior summaries for bot sanity checks."""

from dataclasses import dataclass, field

from combatrl.agents.utility import direction_action_away, get_nearest_enemy
from combatrl.core.geometry import distance
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import EventLog


@dataclass
class BehaviorSummary:
    """Small aggregate summary for one match run."""

    attack_attempt_count: dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0})
    damage_dealt: dict[int, float] = field(default_factory=lambda: {0: 0.0, 1: 0.0})
    retreat_action_count: dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0})
    distance_sample_count: int = 0
    distance_to_nearest_enemy_sum: dict[int, float] = field(
        default_factory=lambda: {0: 0.0, 1: 0.0}
    )

    def observe_actions(self, state: MatchState, actions: list[ActionCommand]) -> None:
        """Record selected action counts from a pre-step state."""
        for action in actions:
            agent = state.agents.get(action.agent_id)
            if agent is None or not agent.alive:
                continue
            if action.action_type == ActionType.ATTACK_NEAREST:
                self.attack_attempt_count[agent.team_id] += 1
            nearest_enemy = get_nearest_enemy(state, action.agent_id)
            if nearest_enemy is not None and action.action_type == direction_action_away(
                agent.position, nearest_enemy.position
            ):
                self.retreat_action_count[agent.team_id] += 1

    def observe_state(self, state: MatchState) -> None:
        """Sample average distance to each live agent's nearest enemy."""
        sampled_any = False
        for agent_id in sorted(state.agents):
            agent = state.agents[agent_id]
            if not agent.alive:
                continue
            nearest_enemy = get_nearest_enemy(state, agent_id)
            if nearest_enemy is None:
                continue
            self.distance_to_nearest_enemy_sum[agent.team_id] += distance(
                agent.position,
                nearest_enemy.position,
            )
            sampled_any = True
        if sampled_any:
            self.distance_sample_count += 1

    def observe_events(self, state: MatchState, events: list[EventLog]) -> None:
        """Record damage from simulator events."""
        _ = state
        for event in events:
            if event.event_type != "agent_damaged" or event.source_agent_id is None:
                continue
            source = state.agents.get(event.source_agent_id)
            if source is None:
                continue
            damage = event.payload.get("damage", 0.0)
            self.damage_dealt[source.team_id] += float(damage)

    def final_total_hp(self, state: MatchState) -> dict[int, float]:
        """Return final total HP by team."""
        totals = {0: 0.0, 1: 0.0}
        for agent in state.agents.values():
            totals[agent.team_id] += agent.hp
        return totals

    def average_distance_to_nearest_enemy(self) -> dict[int, float]:
        """Return sampled average nearest-enemy distance by team."""
        if self.distance_sample_count == 0:
            return {0: 0.0, 1: 0.0}
        return {
            team_id: distance_sum / self.distance_sample_count
            for team_id, distance_sum in self.distance_to_nearest_enemy_sum.items()
        }
