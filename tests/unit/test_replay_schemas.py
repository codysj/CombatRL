import pytest
from pydantic import ValidationError

from combatrl.core.constants import REPLAY_SCHEMA_VERSION
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.replay import EventLog, ReplayFrame, make_event_log
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.snapshots import build_replay_frame


def test_event_log_validates() -> None:
    event = EventLog(
        event_id="match:tick-0:event-0",
        tick=0,
        event_type="match_started",
        source_agent_id=None,
        target_agent_id=None,
        payload={"seed": 42},
    )

    assert event.tick == 0


def test_replay_frame_validates() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)
    event = make_event_log(
        match_id=engine.state.match_id,
        tick=0,
        index=0,
        event_type="match_started",
    )

    frame = build_replay_frame(engine.state, [event])

    assert frame.replay_schema_version == REPLAY_SCHEMA_VERSION
    assert frame.tick == 0


def test_frame_event_tick_mismatch_fails() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)
    bad_event = make_event_log(
        match_id=engine.state.match_id,
        tick=1,
        index=0,
        event_type="match_started",
    )

    with pytest.raises(ValidationError):
        ReplayFrame(
            replay_schema_version=REPLAY_SCHEMA_VERSION,
            match_id=engine.state.match_id,
            tick=0,
            sim_time_seconds=0.0,
            agents=[engine.state.agents[agent_id] for agent_id in sorted(engine.state.agents)],
            events=[bad_event],
            scoreboard={},
        )


def test_snapshot_helper_sorts_agents_by_agent_id() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)
    reversed_agents = dict(reversed(list(engine.state.agents.items())))
    engine.state.agents = reversed_agents

    frame = build_replay_frame(engine.state, [])

    assert [agent.agent_id for agent in frame.agents] == sorted(engine.state.agents)
