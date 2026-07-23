"""
mcp_agent.py - The host/agent. Same principle as mcp_poc.py, but the tool now
lives in a REAL MCP server (mcp_server.py) instead of a local dict. The tool is
discovered and executed over the MCP protocol; only that transport changed.

Flow (printed as [LABELS] when you run it):
  1. Launch + connect to the MCP server, DISCOVER its tools (session.list_tools).
  2. Give the query + tool catalog to the model (llama-server on :8080). The
     model is the brain: it decides whether / which tool to call.
  3. Execute the chosen tool THROUGH MCP (session.call_tool).
  4. Feed the result back to the model for the final answer.

Model-agnostic: it only talks to the OpenAI-compatible endpoint, so whatever
model llama-server serves works. The tool decision uses a lenient JSON prompt so
it works even with models that lack native function-calling.

Requires: pip install mcp numpy requests
Run (llama-server must be up on :8080):
    python experiments/mcp_agent.py
    python experiments/mcp_agent.py "cuanto es la raiz cuadrada de 144"
"""

import os
import sys
import re
import json
import asyncio

import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

LLM_URL = "http://localhost:8080/v1/chat/completions"
SERVER_PATH = os.path.join(os.path.dirname(__file__), "mcp_server.py")


def ask_llm(messages):
    """Send messages to the OpenAI-compatible endpoint and return the text."""
    r = requests.post(LLM_URL, json={
        "messages": messages,
        "temperature": 0,
        "stream": False,
    })
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def parse_tool_call(text, tool_names):
    """Return {'tool':..., 'args':...} if the model asked for a known tool, else None."""
    candidates = [text.strip()]
    m = re.search(r"\{.*\}", text, re.DOTALL)  # first '{' to last '}'
    if m:
        candidates.append(m.group(0))
    for c in candidates:
        try:
            obj = json.loads(c)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("tool") in tool_names:
            return obj
    return None


async def main(query):
    params = StdioServerParameters(command=sys.executable, args=[SERVER_PATH])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # STEP 1 - discover the tools over MCP.
            listed = await session.list_tools()
            tools = listed.tools
            names = {t.name for t in tools}
            catalog = "\n".join(
                f'- {t.name}({", ".join(t.inputSchema.get("properties", {}).keys())}): '
                f'{(t.description or "").strip()}'
                for t in tools
            )
            print(f"\n[MCP] tools descubiertas: {', '.join(names)}\n")

            system = (
                "Sos un asistente con acceso a herramientas.\n\n"
                f"Herramientas:\n{catalog}\n\n"
                "Si necesitas una herramienta responde SOLO con un JSON de una linea, sin texto extra:\n"
                '{"tool": "calcular", "args": {"expresion": "2*2"}}\n'
                "Si no necesitas ninguna, responde normalmente en texto."
            )
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": query},
            ]
            print(f"[USUARIO] {query}\n")

            # STEP 2 - the model decides.
            decision = ask_llm(messages)
            print(f"[MODELO decide] {decision.strip()}\n")

            call = parse_tool_call(decision, names)
            if not call:
                print(f"[RESPUESTA FINAL] {decision.strip()}")
                return

            # STEP 3 - execute the tool THROUGH MCP.
            print(f"[HOST -> MCP] call_tool {call['tool']}({call.get('args', {})})")
            result = await session.call_tool(call["tool"], arguments=call.get("args", {}))
            text = result.content[0].text if result.content else ""
            print(f"[MCP -> HOST] resultado = {text}\n")

            # STEP 4 - feed the result back for the final answer.
            messages.append({"role": "assistant", "content": decision})
            messages.append({"role": "user",
                             "content": f"Resultado de {call['tool']} = {text}. "
                                        "Responde al usuario en lenguaje natural."})
            final = ask_llm(messages)
            print(f"[RESPUESTA FINAL] {final.strip()}")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Cuanto es 2x2?"
    asyncio.run(main(q))
