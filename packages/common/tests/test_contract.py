"""Contract tests: lock the shape of the shared chat completions models."""

import json
from pathlib import Path

import pytest
from common.contract import ChatCompletionRequest, ChatCompletionResponse
from pydantic import ValidationError

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_response_validates_against_real_llama_cpp_capture() -> None:
    """A real llama.cpp response -- including its extra, unmodeled fields -- must validate."""
    raw = json.loads((FIXTURES_DIR / "chat_completion_response.json").read_text())

    response = ChatCompletionResponse.model_validate(raw)

    assert response.id == raw["id"]
    assert response.model == raw["model"]
    assert response.usage.total_tokens == raw["usage"]["total_tokens"]
    assert response.choices[0].message.content == raw["choices"][0]["message"]["content"]
    assert response.choices[0].finish_reason == "stop"


def test_response_round_trips_through_json() -> None:
    """Serializing must emit exactly the Phase 0 subset -- no backend-specific extras like
    `timings` -- and re-validating that output must reproduce an identical model."""
    raw = json.loads((FIXTURES_DIR / "chat_completion_response.json").read_text())

    response = ChatCompletionResponse.model_validate(raw)
    dumped = json.loads(response.model_dump_json())

    assert set(dumped.keys()) == {"id", "model", "choices", "usage"}
    assert ChatCompletionResponse.model_validate(dumped) == response


def test_request_accepts_minimal_payload() -> None:
    """The smallest valid request: just model and a single user message."""
    request = ChatCompletionRequest.model_validate(
        {"model": "any", "messages": [{"role": "user", "content": "Say hi"}]}
    )

    assert request.max_tokens is None
    assert request.temperature is None
    assert request.stream is False


def test_request_tolerates_unknown_fields() -> None:
    """Extra fields from real OpenAI-compatible clients (e.g. top_p) must not break validation."""
    request = ChatCompletionRequest.model_validate(
        {
            "model": "any",
            "messages": [{"role": "user", "content": "hi"}],
            "top_p": 0.9,
            "presence_penalty": 0.1,
        }
    )

    assert request.model == "any"


def test_request_rejects_streaming() -> None:
    """stream=true must fail validation instead of being silently dropped."""
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(
            {"model": "any", "messages": [{"role": "user", "content": "hi"}], "stream": True}
        )
