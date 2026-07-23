"""
mcp_poc.py - Minimal proof-of-concept of the agent + tool flow.

Goal: make the "model decides -> tool executes -> model answers" flow visible,
in a single runnable file. It is model-agnostic: it only talks to the local
llama-server OpenAI-compatible endpoint, so whatever model is being served works.

Who does what (printed as [LABELS] when you run it):
  - THE MODEL   (llm at :8080): the brain. Decides whether a tool is needed.
  - THE TOOLS   (TOOLS dict)  : stands in for an MCP server. Dumb - just executes.
  - THIS SCRIPT (the host)    : moves messages between the model and the tools.

In a real setup the tools would live in a SEPARATE MCP server process, and this
host would discover them over the MCP protocol instead of reading a local dict.
The decision logic (the model) and the message-passing (the host) would be
exactly the same - only the transport to the tools changes. That is why MCP is
"just plumbing": the intelligence stays in the model either way.

Run (with the llama-server already running on :8080):
    python experiments/mcp_poc.py
    python experiments/mcp_poc.py "cuanto es la raiz cuadrada de 144"

Requires: pip install requests numpy
"""

import sys
import re
import json
import requests
import numpy as np

LLM_URL = "http://localhost:8080/v1/chat/completions"


# --- The "MCP server" stand-in: a registry of tools. No brains, just executes. ---

def calcular(expresion: str):
    """Evaluate a math expression with numpy available as `np`.

    NOTE: eval is used only for this PoC and is locked to no builtins + np.
    Do not use eval like this in real code.
    """
    return float(eval(expresion, {"__builtins__": {}}, {"np": np}))


TOOLS = {
    "calcular": {
        "func": calcular,
        "description": "Evalua una expresion matematica en Python/numpy. "
                       "Usa sintaxis Python: '2*2', 'np.sqrt(16)', '10/3'.",
        "args": ["expresion"],
    },
}


def tools_catalog():
    return "\n".join(
        f'- {name}({", ".join(t["args"])}): {t["description"]}'
        for name, t in TOOLS.items()
    )


SYSTEM = f"""Sos un asistente con acceso a herramientas.

Herramientas disponibles:
{tools_catalog()}

Si necesitas una herramienta, responde SOLO con un JSON de una linea, sin texto extra:
{{"tool": "calcular", "args": {{"expresion": "2*2"}}}}

Si no necesitas ninguna herramienta, responde normalmente en texto.
"""


def ask_llm(messages):
    """Send messages to the OpenAI-compatible endpoint and return the text."""
    r = requests.post(LLM_URL, json={
        "messages": messages,
        "temperature": 0,
        "stream": False,
    })
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def try_parse_tool_call(text):
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
        if isinstance(obj, dict) and obj.get("tool") in TOOLS:
            return obj
    return None


def run(user_query):
    print(f"\n[USUARIO] {user_query}\n")
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_query},
    ]

    # STEP 1 - the model sees the query + the tool catalog and decides.
    decision = ask_llm(messages)
    print(f"[MODELO decide] {decision.strip()}\n")

    call = try_parse_tool_call(decision)
    if not call:
        # The model answered directly - no tool needed.
        print(f"[RESPUESTA FINAL] {decision.strip()}")
        return

    # STEP 2 - the host routes the call to the tool.
    #          (In a real setup this hop travels over the MCP protocol.)
    name = call["tool"]
    args = call.get("args", {})
    print(f"[HOST -> tool] ejecutando {name}({args})")
    result = TOOLS[name]["func"](**args)
    print(f"[tool -> HOST] resultado = {result}\n")

    # STEP 3 - feed the result back to the model for the final answer.
    messages.append({"role": "assistant", "content": decision})
    messages.append({"role": "user",
                     "content": f"Resultado de {name} = {result}. Responde al usuario en lenguaje natural."})
    final = ask_llm(messages)
    print(f"[RESPUESTA FINAL] {final.strip()}")


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Cuanto es 2x2?"
    run(query)
