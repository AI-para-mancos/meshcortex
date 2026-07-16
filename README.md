# meshcortex
Self-hosted, backend-agnostic LLM orchestrator — routes requests across GPU and Raspberry Pi edge nodes via an OpenAI-compatible API, with MCP tools and RAG built in

## Repository structure

This project is a **monorepo**: a single git repository containing multiple packages, managed as a Python workspace (uv workspaces).

```text
meshcortex/
  packages/
    orchestrator/       # Gateway/router, backend-agnostic core
    backends/           # Grouping folder for inference-node packages (no shared code/deps)
      gpu-node/         # GPU inference backend (vLLM/llama.cpp) — own pyproject.toml, CUDA deps
      edge-pi-node/     # Raspberry Pi 5 edge inference backend — own pyproject.toml, ARM deps
    mcp-layer/          # MCP servers exposing orchestrator functionality
  configs/
    models.yaml         # Shared model registry: name, quantization, size, compatible node type, source URL
  pyproject.toml        # Workspace root
  README.md
```

Each leaf package (`orchestrator`, `gpu-node`, `edge-pi-node`, `mcp-layer`) is independently installable/testable, but the whole repo shares one version history, one CI pipeline, and one set of lint/format rules. This replaces the earlier multi-repo plan (separate repos synced via version tags).

`backends/` is a grouping folder, not a shared package: `gpu-node` and `edge-pi-node` each keep their own `pyproject.toml` because their dependencies are incompatible (CUDA/vLLM vs. ARM/CPU-only llama.cpp — neither installs on the other's machine). Grouping them under `backends/` just reflects that both are "model-running nodes," conceptually separate from `orchestrator` and `mcp-layer`. Model weights are never committed: each node downloads/caches its own weights locally (gitignored), keyed against the single shared manifest in `configs/models.yaml`.
