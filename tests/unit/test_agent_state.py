import pytest
from pydantic import ValidationError

from combatrl.schemas.agent_state import AgentState


def make_agent_state(**overrides: object) -> AgentState:
    values: dict[str, object] = {
        "agent_id": "team0_tank_0",
        "team_id": 0,
        "role": "tank",
        "position": (10.0, 20.0),
        "velocity": (0.0, 0.0),
        "hp": 160.0,
        "max_hp": 160.0,
        "alive": True,
        "attack_cooldown_ticks": 0,
        "ability_cooldown_ticks": 0,
        "status_effects": [],
        "current_target_id": None,
        "last_action_id": None,
    }
    values.update(overrides)
    return AgentState.model_validate(values)


def test_valid_tank_agent_state_passes() -> None:
    agent = make_agent_state()

    assert agent.agent_id == "team0_tank_0"


def test_hp_below_zero_fails() -> None:
    with pytest.raises(ValidationError):
        make_agent_state(hp=-1.0, alive=False)


def test_hp_above_max_hp_fails() -> None:
    with pytest.raises(ValidationError):
        make_agent_state(hp=161.0)


def test_negative_cooldown_fails() -> None:
    with pytest.raises(ValidationError):
        make_agent_state(attack_cooldown_ticks=-1)


def test_alive_mismatch_fails() -> None:
    with pytest.raises(ValidationError):
        make_agent_state(hp=0.0, alive=True)
