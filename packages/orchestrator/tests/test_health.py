"""Tests for GET /health."""

import httpx


async def test_health_returns_ok(client: httpx.AsyncClient) -> None:
    """The liveness endpoint is trivially checkable: always 200, always this body."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
