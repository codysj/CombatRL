"""Natural-language-to-behavior-profile parsing."""

from combatrl.nlp.parser import parse_command_to_profile
from combatrl.schemas.nlp import BehaviorProfileParseResult

__all__ = ["BehaviorProfileParseResult", "parse_command_to_profile"]
