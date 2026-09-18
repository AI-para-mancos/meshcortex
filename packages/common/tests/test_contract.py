"""Contract tests: lock the shape of the shared chat completions models."""

import json
from pathlib import Path

import pytest
from common.contract import (
    AUTO_MODEL,
    ChatCompletionRequest,
    ChatCompletionResponse,
    is_auto_selection,
)
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
    assert response.node_id is None


def test_response_round_trips_through_json() -> None:
    """Serializing must emit exactly the Phase 0 subset -- no backend-specific extras like
    `timings` -- and re-validating that output must reproduce an identical model."""
    raw = json.loads((FIXTURES_DIR / "chat_completion_response.json").read_text())

    response = ChatCompletionResponse.model_validate(raw)
    dumped = json.loads(response.model_dump_json())

    assert set(dumped.keys()) == {"id", "model", "choices", "usage", "node_id"}
    assert ChatCompletionResponse.model_validate(dumped) == response


def test_response_keeps_the_serving_node() -> None:
    """A backend that reports its identity must have it survive validation and serialization."""
    raw = json.loads((FIXTURES_DIR / "chat_completion_response.json").read_text())
    raw["node_id"] = "gpu-01"

    response = ChatCompletionResponse.model_validate(raw)

    assert response.node_id == "gpu-01"
    assert json.loads(response.model_dump_json())["node_id"] == "gpu-01"


def test_response_rejects_the_sentinel() -> None:
    """Answering 'auto' would hide which model actually served."""
    raw = json.loads((FIXTURES_DIR / "chat_completion_response.json").read_text())
    raw["model"] = AUTO_MODEL

    with pytest.raises(ValidationError):
        ChatCompletionResponse.model_validate(raw)


def test_request_accepts_minimal_payload() -> None:
    """The smallest valid request: a single user message, nothing else."""
    request = ChatCompletionRequest.model_validate(
        {"messages": [{"role": "user", "content": "Say hi"}]}
    )

    assert request.model is None
    assert request.max_tokens is None
    assert request.temperature is None
    assert request.stream is False


@pytest.mark.parametrize(
    ("payload", "expected_model", "expected_auto"),
    [
        pytest.param({}, None, True, id="omitted"),
        pytest.param({"model": AUTO_MODEL}, AUTO_MODEL, True, id="sentinel"),
        pytest.param({"model": "qwen3-1.7b-q4"}, "qwen3-1.7b-q4", False, id="named"),
    ],
)
def test_request_accepts_every_way_of_naming_a_model(
    payload: dict, expected_model: str | None, expected_auto: bool
) -> None:
    """Omitting `model` and sending the sentinel are the same request; a real name is not."""
    request = ChatCompletionRequest.model_validate(
        {"messages": [{"role": "user", "content": "hi"}], **payload}
    )

    assert request.model == expected_model
    assert is_auto_selection(request.model) is expected_auto


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
