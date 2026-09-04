"""Shared fixtures: an in-process orchestrator app backed by a test registry."""

import textwrap
from pathlib import Path

import httpx
import pytest
from orchestrator.main import app
from orchestrator.settings import settings

FAKE_BACKEND_URL = "http://backend.test"
TEST_MODEL = "Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M"


@pytest.fixture
def backend_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:
    """Point the orchestrator at a test registry whose only model maps to a fake
    backend URL that respx can intercept."""
    registry_file = tmp_path / "models.yaml"
    registry_file.write_text(
        textwrap.dedent(f"""\
        backends:
          gpu: {FAKE_BACKEND_URL}
        models:
          - name: "{TEST_MODEL}"
            quantization: Q4_K_M
            size_b: 0.5
            format: gguf
            node_types: [gpu]
            source_url: https://example.test/model.gguf
        """)
    )
    monkeypatch.setattr(settings, "registry_path", registry_file)
    return FAKE_BACKEND_URL


@pytest.fixture
async def client(backend_url: str):
    """An async client talking to the orchestrator app in-process via ASGI.

    Runs the app's lifespan (startup/shutdown) so `app.state.registry` and
    `app.state.http_client` exist, exactly as they would under a real server.
    """
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
