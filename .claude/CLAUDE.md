# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

meshcortex is a self-hosted, backend-agnostic LLM orchestrator: it routes requests across GPU and edge nodes via an OpenAI-compatible API, with MCP tools and RAG built in.

## Repository structure

This is a Python monorepo managed as a **uv workspace**. The root `pyproject.toml` is a *virtual* workspace root (`[tool.uv] package = false`) — it is not itself an installable package, just a workspace declaration.

```
meshcortex/
  packages/
    orchestrator/       # Gateway/router, backend-agnostic core
    backends/           # Grouping folder for inference-node packages (no shared code/deps)
      gpu-node/         # GPU inference backend (vLLM/llama.cpp) — own pyproject.toml, CUDA deps
      edge-node/        # planned: edge inference backend, ARM deps
    mcp-layer/          # planned: MCP servers exposing orchestrator functionality
  configs/              # Shared config, e.g. the model registry (name, quantization, size, node type, source URL)
  pyproject.toml        # Workspace root
```

Each leaf package (`orchestrator`, `gpu-node`, and later `edge-node`, `mcp-layer`) has its own `pyproject.toml` and is independently installable/testable, with its own (possibly incompatible) dependencies — `gpu-node` and `edge-node` will never share a dependency set (CUDA/vLLM vs. ARM/CPU-only llama.cpp).

`backends/` packages share a Python **namespace package** (PEP 420): `gpu-node` is imported as `backends.gpu_node`, not as a top-level `gpu_node`. This is import-path grouping only — there is no `packages/backends/pyproject.toml` and no shared code or dependencies. Each backend's own `src/backends/<name>/` directory has no `__init__.py` at the `backends` level (that would turn it into a regular package and break the namespace merge); only the leaf directory (`src/backends/gpu_node/`) has one.

Model weights are never committed: each node downloads/caches its own weights locally (gitignored via `*.gguf`, `*.safetensors`, `models/`), keyed against the shared manifest under `configs/`.

## Commands

- Install/sync the whole workspace: `uv sync` (or `uv sync --all-packages`)
- Sanity-check the workspace wiring: `uv run python -c "import orchestrator, backends.gpu_node"`
- Lint: `uv run ruff check .`
- Format (in place): `uv run ruff format .` — verify only: `uv run ruff format --check .`
- Tests: `uv run pytest packages/ -v`

Lint/format is enforced by `ruff` and runs in CI (`.github/workflows/ci.yml`) and
via pre-commit (`.pre-commit-config.yaml`); the ruff version is pinned to the same
value in both plus the `pyproject.toml` dev group. See `CONTRIBUTING.md` for local
pre-commit setup. Ruff config lives in `[tool.ruff]` in `pyproject.toml`.

Before opening a PR, run the same checks CI runs so lint/format failures are
caught locally instead of after pushing:

```
uv run ruff check .
uv run ruff format --check .
```

## Adding a new workspace package

A new leaf package needs all of the following, or `uv sync` will not install it:

1. `packages/<group>/<name>/pyproject.toml` with a `[project]` table (name, version, `requires-python`), a `[tool.hatch.build.targets.wheel] packages = [...]` entry pointing at its `src/` package, and a hatchling `[build-system]` block.
2. `src/<import_name>/__init__.py` — the import name uses underscores (e.g. `gpu_node`) while the folder/distribution name uses hyphens (e.g. `gpu-node`). For a package under `backends/`, nest it one level deeper — `src/backends/<import_name>/__init__.py` — and set `packages = ["src/backends"]` so it joins the `backends` namespace instead of becoming a top-level import.
3. An entry in the root `pyproject.toml`'s `[tool.uv.workspace] members` list.
4. An entry in the root `pyproject.toml`'s `dependencies` plus a matching `[tool.uv.sources]` line (`<name> = { workspace = true }`). Without this last step the package is a recognized workspace *member* but a plain `uv sync` will not install it into the shared `.venv` (only `uv sync --all-packages` would). Note the root `dependencies` entry still uses the distribution name (`gpu-node`), not the import path.

## Conventions

- All code and comments must be written in English. This covers identifiers (variables, functions, classes, modules), comments, docstrings, log/console messages, test names, and documentation. No mixed-language content.
- Do not add links or references to GitHub issues (e.g. issue numbers, `#123`) anywhere in this repo's code, comments, or docs.

## Local notes

Personal, machine-specific setup notes (build quirks, local paths, one-off fixes) belong in `CLAUDE.local.md`, which is gitignored — not in this file.
