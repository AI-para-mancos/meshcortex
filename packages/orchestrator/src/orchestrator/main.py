"""Orchestrator FastAPI app: health check and chat completions passthrough."""

from contextlib import asynccontextmanager

import httpx
from common.contract import ChatCompletionRequest, is_auto_selection
from common.registry import load_registry
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from orchestrator.forwarder import forward_chat_completion
from orchestrator.resolution import BackendNotConfiguredError, ModelNotFoundError, resolve_backend
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
    # The sentinel is resolved before any catalog lookup, and nothing resolves it
    # yet. Refuse it here rather than blaming a caller who named nothing.
    if is_auto_selection(request.model):
        return JSONResponse(
            status_code=503,
            content={"error": "automatic model selection is not available yet"},
        )
    try:
        backend_url = resolve_backend(app.state.registry, request.model)
    except ModelNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": f"model '{exc.model}' not found in registry"},
        )
    except BackendNotConfiguredError as exc:
        # The model exists, the cluster just cannot serve it: the caller has nothing to fix.
        return JSONResponse(status_code=503, content={"error": str(exc)})
    return await forward_chat_completion(app.state.http_client, backend_url, request)
