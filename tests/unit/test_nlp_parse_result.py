import pytest
from pydantic import ValidationError

from combatrl.nlp.validation import balanced_profile
from combatrl.schemas.nlp import BehaviorProfileParseResult


def test_success_requires_profile() -> None:
    with pytest.raises(ValidationError, match="successful parse results must include a profile"):
        BehaviorProfileParseResult(
            success=True,
            command="play aggressively",
            profile=None,
            errors=[],
            unsupported_requests=[],
            parser_source="rules",
        )


def test_failure_requires_errors_or_unsupported_requests() -> None:
    with pytest.raises(ValidationError, match="failed parse results"):
        BehaviorProfileParseResult(
            success=False,
            command="",
            profile=None,
            errors=[],
            unsupported_requests=[],
            parser_source="rules",
        )


def test_command_is_preserved() -> None:
    command = "  protect ally and stay together  "
    result = BehaviorProfileParseResult(
        success=True,
        command=command,
        profile=balanced_profile(),
        errors=[],
        unsupported_requests=[],
        parser_source="rules",
    )

    assert result.command == command
