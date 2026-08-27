"""Orchestrator FastAPI app: health check and chat completions passthrough."""

from contextlib import asynccontextmanager

import httpx
from common.contract import ChatCompletionRequest
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from orchestrator.forwarder import forward_chat_completion
from orchestrator.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=settings.backend_timeout_seconds) as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> JSONResponse:
    return await forward_chat_completion(app.state.http_client, request)
