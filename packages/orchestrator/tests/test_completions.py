"""Tests for POST /v1/chat/completions: passthrough happy path and failure modes.

The backend is never real -- every test mocks it with respx -- so this suite
has zero network/GPU/model dependencies and runs in well under a second.
"""

import json
from pathlib import Path

import httpx
from common.contract import ChatCompletionResponse
from respx import MockRouter

FIXTURES_DIR = Path(__file__).parent / "fixtures"

REQUEST_PAYLOAD = {
    "model": "Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M",
    "messages": [{"role": "user", "content": "Explain recursion briefly."}],
}


def _load_canned_response() -> dict:
    """A real llama.cpp response, captured for the shared contract (see #7)."""
    return json.loads((FIXTURES_DIR / "chat_completion_response.json").read_text())


async def test_happy_path_returns_backend_response(
    client: httpx.AsyncClient, backend_url: str, respx_mock: MockRouter
) -> None:
    """Contract in, contract out: a successful backend call is passed through as-is."""
    respx_mock.post(f"{backend_url}/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=_load_canned_response())
    )

    response = await client.post("/v1/chat/completions", json=REQUEST_PAYLOAD)

    assert response.status_code == 200
    ChatCompletionResponse.model_validate(response.json())


async def test_backend_unreachable_returns_502(
    client: httpx.AsyncClient, backend_url: str, respx_mock: MockRouter
) -> None:
    """A connection failure to the backend surfaces as a clean 502, not a stack trace."""
    respx_mock.post(f"{backend_url}/v1/chat/completions").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    response = await client.post("/v1/chat/completions", json=REQUEST_PAYLOAD)

    assert response.status_code == 502
    assert backend_url in response.json()["detail"]


async def test_backend_error_is_passed_through(
    client: httpx.AsyncClient, backend_url: str, respx_mock: MockRouter
) -> None:
    """A backend-side error is forwarded as-is (status + body), never swallowed or rewrapped."""
    respx_mock.post(f"{backend_url}/v1/chat/completions").mock(
        return_value=httpx.Response(500, json={"error": "internal backend failure"})
    )

    response = await client.post("/v1/chat/completions", json=REQUEST_PAYLOAD)

    assert response.status_code == 500
    assert response.json() == {"error": "internal backend failure"}


async def test_forwarded_payload_matches_the_request(
    client: httpx.AsyncClient, backend_url: str, respx_mock: MockRouter
) -> None:
    """The orchestrator must not silently mutate the request on its way to the backend."""
    route = respx_mock.post(f"{backend_url}/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=_load_canned_response())
    )

    await client.post("/v1/chat/completions", json=REQUEST_PAYLOAD)

    forwarded_body = json.loads(route.calls.last.request.content)
    assert forwarded_body["model"] == REQUEST_PAYLOAD["model"]
    assert forwarded_body["messages"] == REQUEST_PAYLOAD["messages"]
    assert forwarded_body["stream"] is False


async def test_unknown_model_returns_404(client: httpx.AsyncClient, backend_url: str) -> None:
    """A model absent from the registry yields a 404 with a helpful message."""
    response = await client.post(
        "/v1/chat/completions",
        json={"model": "no-such-model", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 404
    assert response.json() == {"error": "model 'no-such-model' not found in registry"}
