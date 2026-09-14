"""Shared /v1/chat/completions contract for meshcortex.

This module is the single source of truth for the OpenAI-compatible chat
completions request/response shape used across the orchestrator and every
backend (vLLM, llama.cpp, ...). It intentionally models only the Phase 0
subset of the real OpenAI schema -- see each field's description for exactly
what is and isn't covered.

Streaming (`stream=true`) is explicitly out of scope for Phase 0. The
`ChatCompletionRequest.stream` field only accepts `false`; sending `true`
raises a validation error instead of being silently accepted and ignored.

Omitting `model` and sending the reserved value `auto` are the same request:
both let the cluster choose. The sentinel is resolved to a concrete name
*before* any catalog lookup. Whoever chose the model owns the right to
substitute it -- a cluster-chosen model may fall back, a caller-named one is
served or refused but never swapped.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Role = Literal["system", "user", "assistant"]
AUTO_MODEL = "auto"


def is_auto_selection(model: str | None) -> bool:
    """Whether the caller left the choice of model to the cluster.

    One predicate, so the omitted/sentinel equivalence cannot drift between call
    sites.
    """
    return model is None or model == AUTO_MODEL


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

    model: str | None = Field(
        default=None,
        description=(
            "Model identifier requested by the client. Omit it, or send the reserved value "
            "'auto', to let the cluster choose -- the two are equivalent."
        ),
    )
    messages: list[Message] = Field(description="Conversation so far, oldest message first.")
    max_tokens: int | None = Field(
        default=None, description="Upper bound on generated tokens. None lets the backend decide."
    )
    temperature: float | None = Field(
        default=None, description="Sampling temperature. None lets the backend decide."
    )
    stream: bool = Field(
        default=False, description="Must be false. Streaming is out of scope for Phase 0."
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
    finish_reason: str | None = Field(description="Why generation stopped, e.g. 'stop'/'length'.")


class ChatCompletionResponse(ContractModel):
    """Response body for POST /v1/chat/completions (Phase 0 subset)."""

    id: str = Field(description="Unique identifier for this completion.")
    model: str = Field(
        description="Concrete model that produced the completion. Never the 'auto' sentinel."
    )
    choices: list[Choice] = Field(description="Generated choices.")
    usage: Usage = Field(description="Token accounting. Mandatory, see Usage docstring.")
    node_id: str | None = Field(
        default=None,
        description=(
            "Node that served the request. Unset when the backend reports no identity. Mirrors "
            "the error shape, so a success can also say where it ran."
        ),
    )

    @field_validator("model")
    @classmethod
    def _reject_sentinel(cls, value: str) -> str:
        """Echoing the sentinel back would hide which model actually served."""
        if value == AUTO_MODEL:
            raise ValueError(
                f"'{AUTO_MODEL}' is not a valid response model; report the model that served."
            )
        return value
