"""Natural-language-to-BehaviorProfile parser entry points."""

from __future__ import annotations

import json
from collections.abc import Callable

from combatrl.nlp.fallback_rules import parse_with_rules
from combatrl.nlp.prompts import build_profile_parser_prompt
from combatrl.nlp.validation import validate_parsed_profile
from combatrl.schemas.nlp import BehaviorProfileParseResult
from combatrl.schemas.profiles import BehaviorProfile


def parse_command_to_profile(
    command: str,
    base_profile: BehaviorProfile | None = None,
    use_llm: bool = False,
    llm_client: Callable[[str], str] | None = None,
) -> BehaviorProfileParseResult:
    """Translate natural language into a validated BehaviorProfile."""
    if not use_llm:
        return parse_with_rules(command, base_profile=base_profile)

    if llm_client is None:
        result = parse_with_rules(command, base_profile=base_profile)
        return result.model_copy(
            update={
                "parser_source": "fallback",
                "notes": "LLM parsing requested without llm_client; used deterministic rules.",
            }
        )

    prompt = build_profile_parser_prompt(command, base_profile=base_profile)
    try:
        raw_output = llm_client(prompt)
    except Exception as exc:
        return BehaviorProfileParseResult(
            success=False,
            command=command,
            profile=None,
            errors=[f"llm_client failed: {exc}"],
            unsupported_requests=[],
            parser_source="llm",
            raw_output=None,
        )

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        return BehaviorProfileParseResult(
            success=False,
            command=command,
            profile=None,
            errors=[f"invalid JSON from llm_client: {exc.msg}"],
            unsupported_requests=[],
            parser_source="llm",
            raw_output=raw_output,
        )
    if not isinstance(parsed, dict):
        return BehaviorProfileParseResult(
            success=False,
            command=command,
            profile=None,
            errors=["LLM output must be a JSON object"],
            unsupported_requests=[],
            parser_source="llm",
            raw_output=raw_output,
        )

    candidate = dict(parsed)
    candidate["command"] = command
    result = validate_parsed_profile(candidate, base_profile=base_profile, parser_source="llm")
    return result.model_copy(update={"raw_output": raw_output})


__all__ = ["BehaviorProfileParseResult", "parse_command_to_profile"]
