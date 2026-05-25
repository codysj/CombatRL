import pytest
from pydantic import ValidationError

from combatrl.schemas.actions import ActionCommand, ActionType


def test_action_command_accepts_valid_action() -> None:
    command = ActionCommand(agent_id="team0_tank_0", action_type=ActionType.MOVE_UP)

    assert command.action_type == ActionType.MOVE_UP


def test_action_command_rejects_unknown_action() -> None:
    with pytest.raises(ValidationError):
        ActionCommand.model_validate({"agent_id": "team0_tank_0", "action_type": "TELEPORT"})
