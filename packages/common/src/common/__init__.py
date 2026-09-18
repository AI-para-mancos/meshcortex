"""Shared contract types used by both the orchestrator and every backend."""

from common.contract import (
    AUTO_MODEL,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    Message,
    Role,
    Usage,
    is_auto_selection,
)

__all__ = [
    "AUTO_MODEL",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "Choice",
    "Message",
    "Role",
    "Usage",
    "is_auto_selection",
]
