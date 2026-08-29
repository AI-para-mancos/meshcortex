import httpx
import pytest
from common.contract import ChatCompletionResponse
from helpers import CHAT_COMPLETIONS_PATH, PROMPT, RawCompletion, orchestrator_request
from settings import IntegrationSettings

pytestmark = pytest.mark.integration

UNKNOWN_MODEL = "definitely-not-a-registered-model"


def test_health_reports_ok(client: httpx.Client, settings: IntegrationSettings) -> None:
    response = orchestrator_request(client, "GET", f"{settings.orchestrator_url}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_completion_matches_the_shared_contract(raw_completion: RawCompletion) -> None:
    """A response off a real engine -- extra unmodeled fields and all -- must validate."""
    ChatCompletionResponse.model_validate(raw_completion.body)


def test_usage_accounts_for_every_token(completion: ChatCompletionResponse) -> None:
    usage = completion.usage

    assert usage.prompt_tokens > 0
    assert usage.completion_tokens > 0
    assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens


def test_completion_returns_non_empty_content(completion: ChatCompletionResponse) -> None:
    assert completion.choices
    assert completion.choices[0].message.content.strip()


def test_completion_reports_the_requested_model(
    completion: ChatCompletionResponse, settings: IntegrationSettings
) -> None:
    """The backend answers under the registry name, not the weights file it loaded."""
    assert completion.model == settings.model


def test_unknown_model_is_rejected(client: httpx.Client, settings: IntegrationSettings) -> None:
    """An unregistered model must not reach a backend that would happily answer anyway."""
    payload = {
        "model": UNKNOWN_MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 1,
    }
    response = orchestrator_request(
        client, "POST", f"{settings.orchestrator_url}{CHAT_COMPLETIONS_PATH}", json=payload
    )

    assert response.status_code == 404
