import pytest
from pydantic import ValidationError

from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.match_state import MatchState


def make_agent() -> AgentState:
    return AgentState(
        agent_id="team0_tank_0",
        team_id=0,
        role="tank",
        position=(10.0, 20.0),
        velocity=(0.0, 0.0),
        hp=160.0,
        max_hp=160.0,
        alive=True,
        attack_cooldown_ticks=0,
        ability_cooldown_ticks=0,
        status_effects=[],
        current_target_id=None,
        last_action_id=None,
    )


def make_match_state(**overrides: object) -> MatchState:
    agent = make_agent()
    values: dict[str, object] = {
        "match_id": "test_seed_1",
        "seed": 1,
        "tick": 0,
        "max_ticks": 10,
        "tick_rate_hz": 20,
        "arena_width": 100.0,
        "arena_height": 60.0,
        "agents": {agent.agent_id: agent},
        "obstacles": [],
        "terminal": False,
        "winner_team_id": None,
        "terminal_reason": None,
    }
    values.update(overrides)
    return MatchState.model_validate(values)


def test_valid_match_state_passes() -> None:
    state = make_match_state()

    assert state.tick == 0


def test_agents_dict_key_mismatch_fails() -> None:
    agent = make_agent()

    with pytest.raises(ValidationError):
        make_match_state(agents={"wrong_id": agent})


def test_terminal_without_terminal_reason_fails() -> None:
    with pytest.raises(ValidationError):
        make_match_state(terminal=True)


def test_tick_beyond_max_ticks_fails() -> None:
    with pytest.raises(ValidationError):
        make_match_state(tick=11)
