from dataclasses import dataclass
from typing import Any

import httpx
import pytest

CHAT_COMPLETIONS_PATH = "/v1/chat/completions"

PROMPT = "Reply with the single word: pong."
MAX_TOKENS = 32

# Enough of a failing body to diagnose from, short enough to read in a CI log.
BODY_EXCERPT_CHARS = 200


@dataclass
class RawCompletion:
    """One live completion and what it cost, before the contract is applied to it."""

    body: dict
    latency_seconds: float


def orchestrator_request(
    client: httpx.Client, method: str, url: str, **kwargs: Any
) -> httpx.Response:
    """Send a request to the orchestrator, failing with a startup hint if it is not up.

    A refused connection is the most common way this suite is run wrong, so it gets a
    message naming the command that fixes it rather than a bare `ConnectError`.
    """
    try:
        return client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        pytest.fail(f"Orchestrator unreachable at {url}: {exc}.")
