import time
from collections.abc import Iterator

import httpx
import pytest
from common.contract import ChatCompletionRequest, ChatCompletionResponse, Message
from helpers import (
    BODY_EXCERPT_CHARS,
    CHAT_COMPLETIONS_PATH,
    MAX_TOKENS,
    PROMPT,
    RawCompletion,
    orchestrator_request,
)
from pydantic import ValidationError
from settings import IntegrationSettings

MEASUREMENT_KEY = pytest.StashKey[str]()


def _format_measurement(completion: RawCompletion, settings: IntegrationSettings) -> str:
    """Summarise what the live completion cost, for the end-of-run report.

    This is latency as the *client* sees it, so it includes the gateway's own overhead.
    The orchestrator's own per-request logging measures the server side; the gap between
    the two is the interesting part, which is why this stays even once that exists.
    """
    usage = completion.body.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    latency = completion.latency_seconds

    summary = f"{settings.model} - {latency:.2f}s"
    if prompt_tokens is None or completion_tokens is None:
        return f"{summary}, token counts missing from the response"

    rate = f", {completion_tokens / latency:.1f} tok/s" if completion_tokens else ""
    return (
        f"{summary}, {prompt_tokens} prompt + {completion_tokens} completion "
        f"= {prompt_tokens + completion_tokens} tokens{rate}"
    )


@pytest.fixture(scope="session")
def settings() -> IntegrationSettings:
    """Read the suite's configuration from the environment, or say what is missing.

    Loaded lazily in a fixture rather than at import time: collection happens even for
    a plain `uv run pytest` that deselects these tests, and that must not fail just
    because the environment is not set up for a live run.
    """
    try:
        return IntegrationSettings()
    except ValidationError as exc:
        pytest.fail(
            "Integration settings are incomplete. Set INTEGRATION_MODEL to a model name "
            f"from configs/models.yaml that the running backend serves.\n\n{exc}"
        )


@pytest.fixture(scope="session")
def client(settings: IntegrationSettings) -> Iterator[httpx.Client]:
    with httpx.Client(timeout=settings.timeout_seconds) as session_client:
        yield session_client


@pytest.fixture(scope="session")
def raw_completion(
    client: httpx.Client, settings: IntegrationSettings, pytestconfig: pytest.Config
) -> Iterator[RawCompletion]:
    """Send the single real completion the suite inspects, then record what it cost.

    Session-scoped because generating from a real model is the expensive part of the
    run: every assertion about the response reads this one result.
    """
    request = ChatCompletionRequest(
        model=settings.model,
        messages=[Message(role="user", content=PROMPT)],
        max_tokens=MAX_TOKENS,
        temperature=0.0,
    )

    started = time.perf_counter()
    response = orchestrator_request(
        client,
        "POST",
        f"{settings.orchestrator_url}{CHAT_COMPLETIONS_PATH}",
        json=request.model_dump(mode="json"),
    )
    elapsed = time.perf_counter() - started

    # The forwarder turns an unreachable backend into a 502 already naming the backend
    # URL and the connection error, so its detail is passed through rather than restated.
    if response.status_code == 502:
        pytest.fail(response.json().get("detail", "the backend could not be reached"))

    if response.status_code != 200:
        pytest.fail(
            f"{CHAT_COMPLETIONS_PATH} returned HTTP {response.status_code}, expected 200: "
            f"{response.text[:BODY_EXCERPT_CHARS]}"
        )

    completion = RawCompletion(body=response.json(), latency_seconds=elapsed)
    yield completion
    pytestconfig.stash[MEASUREMENT_KEY] = _format_measurement(completion, settings)


@pytest.fixture(scope="session")
def completion(raw_completion: RawCompletion) -> ChatCompletionResponse:
    """The live completion parsed through the shared contract."""
    return ChatCompletionResponse.model_validate(raw_completion.body)


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Report the measurement where it gets read: the end of the run, pass or fail.

    Printed rather than written to a file so an ordinary run leaves nothing behind.
    """
    measurement = terminalreporter.config.stash.get(MEASUREMENT_KEY, None)
    if measurement is not None:
        terminalreporter.write_sep("-", "measured")
        terminalreporter.write_line(measurement)
