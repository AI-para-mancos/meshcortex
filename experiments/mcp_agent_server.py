"""
mcp_agent_server.py - Exposes the mcp_agent.py tool-calling flow over a
minimal HTTP endpoint, so remote clients (teammates) can trigger it over the
network instead of running the script locally.

Built on Starlette + uvicorn: both already ship as dependencies of the `mcp`
package (FastMCP's HTTP transports need them), so this needs no dependency
beyond what mcp_agent.py already requires.

Auth: if MCP_DEMO_API_KEY is set, requests must send a matching
`Authorization: Bearer <key>` header.

Requires: pip install "mcp<2" numpy requests
Run (llama-server must be up on :8080):
    $env:MCP_DEMO_API_KEY = "changeme"
    python experiments/mcp_agent_server.py
"""

import os

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from mcp_agent import main as run_agent

API_KEY = os.environ.get("MCP_DEMO_API_KEY")


def check_auth(request):
    if not API_KEY:
        return True
    return request.headers.get("authorization") == f"Bearer {API_KEY}"


async def ask(request: Request):
    if not check_auth(request):
        return JSONResponse({"error": "invalid API key"}, status_code=401)

    body = await request.json()
    query = body.get("query")
    if not query:
        return JSONResponse({"error": "missing 'query'"}, status_code=400)

    answer = await run_agent(query)
    return JSONResponse({"answer": answer})


app = Starlette(routes=[Route("/ask", ask, methods=["POST"])])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8211)
