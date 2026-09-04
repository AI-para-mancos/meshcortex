"""Shared fixtures: an in-process orchestrator app pointed at a fake backend URL."""

import httpx
import pytest
from orchestrator.main import app
from orchestrator.settings import settings

FAKE_BACKEND_URL = "http://backend.test"


@pytest.fixture
def backend_url(monkeypatch: pytest.MonkeyPatch) -> str:
    """Point the orchestrator at a fake backend URL that respx can intercept."""
    monkeypatch.setattr(settings, "backend_url", FAKE_BACKEND_URL)
    return FAKE_BACKEND_URL


@pytest.fixture
async def client(backend_url: str):
    """An async client talking to the orchestrator app in-process via ASGI.

    Runs the app's lifespan (startup/shutdown) so `app.state.http_client`
    exists, exactly as it would under a real server.
    """
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
