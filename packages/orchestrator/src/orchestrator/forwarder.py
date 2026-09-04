"""Forwards chat completion requests to a resolved inference backend."""

import httpx
from common.contract import ChatCompletionRequest
from fastapi import HTTPException
from fastapi.responses import JSONResponse

CHAT_COMPLETIONS_PATH = "/v1/chat/completions"


async def forward_chat_completion(
    client: httpx.AsyncClient, backend_url: str, request: ChatCompletionRequest
) -> JSONResponse:
    """Forward a validated chat completion request to ``backend_url``.

    Returns the backend's response as-is (status code and JSON body) on
    success or on a backend-side error. Raises `HTTPException(502)` only
    when the backend itself could not be reached.
    """
    try:
        response = await client.post(
            f"{backend_url}{CHAT_COMPLETIONS_PATH}",
            json=request.model_dump(mode="json"),
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502, detail=f"Backend unreachable at {backend_url}: {exc}"
        ) from exc

    try:
        body = response.json()
    except ValueError:
        body = {"detail": response.text}

    return JSONResponse(status_code=response.status_code, content=body)
