import pytest

from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.match_state import MatchState
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.invariants import InvariantViolation, validate_match_state


def initialized_state() -> MatchState:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    return SimulationEngine(config=config, seed=42).state


def replace_agent(state: MatchState, agent: AgentState) -> MatchState:
    agents = dict(state.agents)
    agents[agent.agent_id] = agent
    return state.model_copy(update={"agents": agents})


def test_validate_match_state_accepts_initialized_mvp_state() -> None:
    validate_match_state(initialized_state())


def test_validate_match_state_catches_out_of_bounds_position() -> None:
    state = initialized_state()
    agent = state.agents["team0_tank_0"].model_copy(update={"position": (-1.0, 25.0)})

    with pytest.raises(InvariantViolation, match="team0_tank_0"):
        validate_match_state(replace_agent(state, agent))


def test_validate_match_state_catches_invalid_hp() -> None:
    state = initialized_state()
    original = state.agents["team0_tank_0"]
    agent = AgentState.model_construct(**{**original.model_dump(), "hp": -1.0, "alive": False})

    with pytest.raises(InvariantViolation, match="team0_tank_0"):
        validate_match_state(replace_agent(state, agent))


def test_validate_match_state_catches_negative_cooldown() -> None:
    state = initialized_state()
    original = state.agents["team0_tank_0"]
    agent = AgentState.model_construct(**{**original.model_dump(), "attack_cooldown_ticks": -1})

    with pytest.raises(InvariantViolation, match="team0_tank_0"):
        validate_match_state(replace_agent(state, agent))


def test_validate_match_state_catches_stale_current_target_id() -> None:
    state = initialized_state()
    agent = state.agents["team0_tank_0"].model_copy(update={"current_target_id": "missing"})

    with pytest.raises(InvariantViolation, match="team0_tank_0"):
        validate_match_state(replace_agent(state, agent))


def test_validate_match_state_catches_alive_hp_mismatch() -> None:
    state = initialized_state()
    original = state.agents["team0_tank_0"]
    agent = AgentState.model_construct(**{**original.model_dump(), "hp": 0.0, "alive": True})

    with pytest.raises(InvariantViolation, match="team0_tank_0"):
        validate_match_state(replace_agent(state, agent))
