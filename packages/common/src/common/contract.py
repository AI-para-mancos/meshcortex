"""Shared /v1/chat/completions contract for meshcortex.

This module is the single source of truth for the OpenAI-compatible chat
completions request/response shape used across the orchestrator and every
backend (vLLM, llama.cpp, ...). It intentionally models only the Phase 0
subset of the real OpenAI schema -- see each field's description for exactly
what is and isn't covered.

Streaming (`stream=true`) is explicitly out of scope for Phase 0. The
`ChatCompletionRequest.stream` field only accepts `false`; sending `true`
raises a validation error instead of being silently accepted and ignored.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Role = Literal["system", "user", "assistant"]
"""Phase 0 role subset. `tool`/`function` roles are out of scope until MCP tool-calling lands."""


class ContractModel(BaseModel):
    """Base class for all contract models.

    Unknown fields are ignored rather than rejected, so real clients and real
    backends -- which send extra fields we don't model yet, e.g. llama.cpp's
    `timings` or vLLM-specific extensions -- don't break validation.
    """

    model_config = ConfigDict(extra="ignore")


class Message(ContractModel):
    """A single chat message. Phase 0 models only `role` and `content`, both mandatory."""

    role: Role = Field(description="Who authored the message.")
    content: str = Field(description="Plain-text message content.")


class ChatCompletionRequest(ContractModel):
    """Request body for POST /v1/chat/completions (Phase 0 subset)."""

    model: str = Field(description="Model identifier requested by the client.")
    messages: list[Message] = Field(description="Conversation so far, oldest message first.")
    max_tokens: int | None = Field(
        default=None, description="Upper bound on generated tokens. None lets the backend decide."
    )
    temperature: float | None = Field(
        default=None, description="Sampling temperature. None lets the backend decide."
    )
    stream: bool = Field(
        default=False, description="Must be false. Streaming responses are out of scope for Phase 0."
    )

    @field_validator("stream")
    @classmethod
    def _reject_streaming(cls, value: bool) -> bool:
        """Fail fast: streaming is documented as out of scope, not silently ignored."""
        if value:
            raise ValueError(
                "stream=true is out of scope for Phase 0; only stream=false is supported."
            )
        return value


class Usage(ContractModel):
    """Token accounting for a completion.

    Mandatory on every response: P0-15 (observability) depends on this
    always being present.
    """

    prompt_tokens: int = Field(description="Tokens consumed by the input messages.")
    completion_tokens: int = Field(description="Tokens generated in the response.")
    total_tokens: int = Field(description="prompt_tokens + completion_tokens.")


class Choice(ContractModel):
    """A single completion choice.

    Phase 0 backends are expected to return exactly one choice, but the list
    shape is kept so the contract stays compatible with the real API.
    """

    index: int = Field(description="Position of this choice within the choices list.")
    message: Message = Field(description="The generated assistant message.")
    finish_reason: str | None = Field(description="Why generation stopped, e.g. 'stop' or 'length'.")


class ChatCompletionResponse(ContractModel):
    """Response body for POST /v1/chat/completions (Phase 0 subset)."""

    id: str = Field(description="Unique identifier for this completion.")
    model: str = Field(description="Model that produced the completion.")
    choices: list[Choice] = Field(description="Generated choices.")
    usage: Usage = Field(description="Token accounting. Mandatory, see Usage docstring.")
