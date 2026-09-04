"""Orchestrator FastAPI app: health check and chat completions passthrough."""

from contextlib import asynccontextmanager

import httpx
from common.contract import ChatCompletionRequest
from common.registry import load_registry
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from orchestrator.forwarder import forward_chat_completion
from orchestrator.resolution import ModelNotFoundError, resolve_backend
from orchestrator.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the registry at startup. load_registry raises on a missing or invalid
    # file, so the service fails fast with a clear error instead of starting in a
    # broken state.
    app.state.registry = load_registry(settings.registry_path)
    async with httpx.AsyncClient(timeout=settings.backend_timeout_seconds) as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> JSONResponse:
    try:
        backend_url = resolve_backend(app.state.registry, request.model)
    except ModelNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": f"model '{exc.model}' not found in registry"},
        )
    return await forward_chat_completion(app.state.http_client, backend_url, request)
