# experiments

Scratch scripts used to explore ideas before they become real packages under
`packages/`. Nothing here is installed as part of the uv workspace — these are
throwaway PoCs run directly with `python experiments/<script>.py`, not
production code.

## Contents

### llama.cpp client demo

Minimal client for a locally running `llama-server` (see the llama.cpp build/run
notes in `CLAUDE.local.md`), hitting its OpenAI-compatible `/v1/chat/completions`
endpoint.

- `llama_request.py` — sends a single chat prompt via `requests` and prints the
  reply.
- `payload.json` — the request body used by `request_curl.ps1` (edit the prompt
  here).
- `request_curl.ps1` — sends the same request with `curl.exe`, bypassing
  PowerShell's `curl` alias (`Invoke-WebRequest`), which doesn't support
  `-d @file`.

Run (with `llama-server` up on `:8080`):

```bash
python experiments/llama_request.py
```

```powershell
powershell -ExecutionPolicy Bypass -File experiments\request_curl.ps1
```

### MCP tool-calling demo

Shows the "model decides -> tool executes -> model answers" agent loop, first
with a fake in-process tool registry, then with a real MCP server, to make clear
that MCP only changes the transport, not the logic.

- `mcp_poc.py` — the host + a local `TOOLS` dict standing in for an MCP server.
  The model (via `llama-server`) decides whether to call the `calcular` tool;
  this script executes it directly and feeds the result back.
- `mcp_server.py` — a real (minimal) MCP server exposing the same `calcular`
  tool over the MCP stdio transport. No LLM, no intelligence — it just
  publishes and executes the tool.
- `mcp_agent.py` — the host/agent again, but now it launches `mcp_server.py` as
  a subprocess, discovers its tools over MCP (`session.list_tools`), and calls
  them through MCP (`session.call_tool`) instead of a local dict.

Requires `pip install mcp numpy requests`. Run (with `llama-server` up on
`:8080`):

```bash
python experiments/mcp_poc.py "cuanto es la raiz cuadrada de 144"
python experiments/mcp_agent.py "cuanto es la raiz cuadrada de 144"
```
