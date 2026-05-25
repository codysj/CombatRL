"""Reward calculation for the Gymnasium wrapper."""

from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import EventLog
from combatrl.schemas.rewards import REQUIRED_REWARD_COMPONENTS, RewardBreakdown

DEFAULT_REWARD_CONFIG: dict[str, float] = {
    "win_bonus": 1.0,
    "loss_penalty": 1.0,
    "damage_dealt": 1.0,
    "damage_taken_penalty": 1.0,
    "death_penalty": 1.0,
    "ally_death_penalty": 1.0,
    "invalid_action_penalty": 1.0,
    "time_penalty": 1.0,
}


class RewardBuilder:
    """Compute controlled-agent rewards from state transitions and events."""

    def __init__(self, reward_config: dict[str, float] | None = None) -> None:
        self.reward_config = DEFAULT_REWARD_CONFIG | (reward_config or {})

    def compute(
        self,
        previous_state: MatchState,
        current_state: MatchState,
        events: list[EventLog],
        controlled_agent_id: str,
        invalid_action: bool = False,
    ) -> RewardBreakdown:
        """Compute a reward breakdown without mutating simulator state."""
        previous_agent = previous_state.agents[controlled_agent_id]
        current_agent = current_state.agents[controlled_agent_id]
        controlled_team_id = previous_agent.team_id

        components = {key: 0.0 for key in REQUIRED_REWARD_COMPONENTS}
        components["win_bonus"] = _win_bonus(current_state, controlled_team_id)
        components["loss_penalty"] = _loss_penalty(current_state, controlled_team_id)
        components["damage_dealt"] = _damage_dealt(
            previous_state,
            current_state,
            events,
            controlled_agent_id,
            controlled_team_id,
        )
        components["damage_taken_penalty"] = _damage_taken_penalty(
            previous_state,
            current_state,
            events,
            controlled_agent_id,
        )
        components["death_penalty"] = (
            -0.5 if previous_agent.alive and not current_agent.alive else 0.0
        )
        components["ally_death_penalty"] = _ally_death_penalty(
            previous_state,
            current_state,
            controlled_agent_id,
            controlled_team_id,
        )
        components["invalid_action_penalty"] = -0.02 if invalid_action else 0.0
        components["time_penalty"] = -0.001

        scaled = {
            key: components[key] * self.reward_config.get(key, 1.0)
            for key in REQUIRED_REWARD_COMPONENTS
        }
        total_reward = sum(scaled.values())
        return RewardBreakdown(
            agent_id=controlled_agent_id,
            tick=current_state.tick,
            total_reward=total_reward,
            components=scaled,
        )


def _win_bonus(state: MatchState, controlled_team_id: int) -> float:
    if (
        state.terminal
        and state.terminal_reason == "elimination"
        and state.winner_team_id == controlled_team_id
    ):
        return 1.0
    return 0.0


def _loss_penalty(state: MatchState, controlled_team_id: int) -> float:
    if (
        state.terminal
        and state.terminal_reason == "elimination"
        and state.winner_team_id is not None
        and state.winner_team_id != controlled_team_id
    ):
        return -1.0
    return 0.0


def _damage_dealt(
    previous_state: MatchState,
    current_state: MatchState,
    events: list[EventLog],
    controlled_agent_id: str,
    controlled_team_id: int,
) -> float:
    event_damage = sum(
        float(event.payload.get("damage", 0.0))
        for event in events
        if event.event_type == "agent_damaged"
        and event.source_agent_id == controlled_agent_id
        and event.target_agent_id is not None
        and previous_state.agents[event.target_agent_id].team_id != controlled_team_id
    )
    if event_damage > 0.0 or any(event.event_type == "agent_damaged" for event in events):
        return event_damage / 100.0

    delta_damage = 0.0
    for agent_id, previous_agent in previous_state.agents.items():
        current_agent = current_state.agents[agent_id]
        if previous_agent.team_id != controlled_team_id:
            delta_damage += max(0.0, previous_agent.hp - current_agent.hp)
    return delta_damage / 100.0


def _damage_taken_penalty(
    previous_state: MatchState,
    current_state: MatchState,
    events: list[EventLog],
    controlled_agent_id: str,
) -> float:
    event_damage = sum(
        float(event.payload.get("damage", 0.0))
        for event in events
        if event.event_type == "agent_damaged" and event.target_agent_id == controlled_agent_id
    )
    if event_damage > 0.0 or any(event.event_type == "agent_damaged" for event in events):
        return -event_damage / 150.0

    previous_agent = previous_state.agents[controlled_agent_id]
    current_agent = current_state.agents[controlled_agent_id]
    return -max(0.0, previous_agent.hp - current_agent.hp) / 150.0


def _ally_death_penalty(
    previous_state: MatchState,
    current_state: MatchState,
    controlled_agent_id: str,
    controlled_team_id: int,
) -> float:
    death_count = 0
    for agent_id, previous_agent in previous_state.agents.items():
        if agent_id == controlled_agent_id or previous_agent.team_id != controlled_team_id:
            continue
        current_agent = current_state.agents[agent_id]
        if previous_agent.alive and not current_agent.alive:
            death_count += 1
    return -0.25 * death_count
