"""Replay snapshot helpers for simulator state."""

from combatrl.core.constants import REPLAY_SCHEMA_VERSION
from combatrl.schemas.configs import SimulationConfig
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import EventLog, ReplayFrame, ReplaySummary


def build_scoreboard(state: MatchState) -> dict[str, float | int | str | None]:
    """Build a compact scoreboard from authoritative match state."""
    team0_agents = [agent for agent in state.agents.values() if agent.team_id == 0]
    team1_agents = [agent for agent in state.agents.values() if agent.team_id == 1]
    return {
        "team0_alive": sum(1 for agent in team0_agents if agent.alive),
        "team1_alive": sum(1 for agent in team1_agents if agent.alive),
        "team0_total_hp": sum(agent.hp for agent in team0_agents),
        "team1_total_hp": sum(agent.hp for agent in team1_agents),
        "winner_team_id": state.winner_team_id,
        "terminal_reason": state.terminal_reason,
    }


def build_replay_frame(state: MatchState, events: list[EventLog]) -> ReplayFrame:
    """Build a replay frame with agents sorted by stable ID."""
    return ReplayFrame(
        replay_schema_version=REPLAY_SCHEMA_VERSION,
        match_id=state.match_id,
        tick=state.tick,
        sim_time_seconds=state.tick / state.tick_rate_hz,
        agents=[state.agents[agent_id].model_copy(deep=True) for agent_id in sorted(state.agents)],
        events=events,
        scoreboard=build_scoreboard(state),
    )


def build_replay_summary(
    *,
    config: SimulationConfig,
    state: MatchState,
    frame_count: int,
    event_count: int,
) -> ReplaySummary:
    """Build terminal replay summary from the final match state."""
    scoreboard = build_scoreboard(state)
    return ReplaySummary(
        replay_schema_version=REPLAY_SCHEMA_VERSION,
        match_id=state.match_id,
        scenario_id=config.scenario_id,
        seed=state.seed,
        final_tick=state.tick,
        terminal=state.terminal,
        terminal_reason=state.terminal_reason,
        winner_team_id=state.winner_team_id,
        frame_count=frame_count,
        event_count=event_count,
        team0_alive=int(scoreboard["team0_alive"] or 0),
        team1_alive=int(scoreboard["team1_alive"] or 0),
        team0_total_hp=float(scoreboard["team0_total_hp"] or 0.0),
        team1_total_hp=float(scoreboard["team1_total_hp"] or 0.0),
    )
