"""
mcp_server.py - A real (minimal) MCP server exposing one tool: `calcular`.

This is the TOOL side. It has no LLM and no intelligence - it just publishes a
tool and executes it when asked, over the MCP protocol (stdio transport). The
agent (mcp_agent.py) launches this as a subprocess and talks to it via MCP.

Requires: pip install mcp numpy
"""

import numpy as np
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calc-tools")


@mcp.tool()
def calcular(expresion: str) -> float:
    """Evalua una expresion matematica en Python/numpy.

    Usa sintaxis Python: '2*2', 'np.sqrt(16)', '10/3'.
    (eval is locked to no builtins + np - fine for this PoC, not for real code.)
    """
    return float(eval(expresion, {"__builtins__": {}}, {"np": np}))


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
