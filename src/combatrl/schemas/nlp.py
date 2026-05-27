"""Natural-language profile parser schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from combatrl.schemas.profiles import BehaviorProfile

ParserSource = Literal["rules", "llm", "fallback"]


class BehaviorProfileParseResult(BaseModel):
    """Result of translating one command into a validated behavior profile."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    command: str
    profile: BehaviorProfile | None
    errors: list[str] = Field(default_factory=list)
    unsupported_requests: list[str] = Field(default_factory=list)
    parser_source: ParserSource
    raw_output: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_result(self) -> "BehaviorProfileParseResult":
        if self.success and self.profile is None:
            msg = "successful parse results must include a profile"
            raise ValueError(msg)
        if not self.success and not self.errors and not self.unsupported_requests:
            msg = "failed parse results must include errors or unsupported_requests"
            raise ValueError(msg)
        return self


__all__ = ["BehaviorProfileParseResult", "ParserSource"]
