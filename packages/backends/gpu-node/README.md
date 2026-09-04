# gpu-node

Thin CLI wrapper that downloads a model from the shared registry (`configs/models.yaml`) and
serves it behind the OpenAI-compatible contract, via an inference engine that already speaks
that API. Two engines are supported: llama.cpp (`llama-server`) and Ollama. vLLM is out of
scope for this package — see `configs/README.md` for the manual vLLM setup instead.

## Install

From the repo root:

```bash
uv sync
```

## Usage

```bash
# Download a registry model's weights only, if not already cached.
uv run gpu-node download <model-name>

# Download (if needed) and serve a registry model with a given engine.
uv run gpu-node serve llama-cpp <model-name> [flags]
uv run gpu-node serve ollama <model-name> [flags]
```

Both commands are expected to run from the repo root: `--registry` defaults to
`configs/models.yaml`, resolved relative to the current working directory.

Each engine owns its own flags. See `uv run gpu-node download --help` and
`uv run gpu-node serve <engine> --help` for reference and defaults.

### Prerequisites

- **llama-cpp**: a `llama-server` binary on `PATH`. See
  [`configs/README.md`](../../../configs/README.md#llamacpp) for how to get one.
- **ollama**: an installed and running Ollama service. See
  [`configs/README.md`](../../../configs/README.md#ollama) for setup.

### Download configuration

`download` (and `serve`'s internal download step) call huggingface_hub directly and let it
decide where weights land — its own default cache (normally outside the repo, e.g.
`~/.cache/huggingface/hub`). There are no `gpu-node` flags for auth, cache location, or mirrors;
set the standard Hugging Face environment variables instead, and huggingface_hub picks
them up automatically:

| Variable                    | Purpose                                               |
|-----------------------------|-------------------------------------------------------|
| `HF_TOKEN`                  | Auth for gated repos, instead of `hf auth login`.     |
| `HF_HOME` / `HF_HUB_CACHE`  | Relocate the cache to a different directory.          |
| `HF_HUB_ENABLE_HF_TRANSFER` | Faster downloads via `hf_transfer`.                   |
| `HF_ENDPOINT`               | Point at a mirror instead of `huggingface.co`.        |

`download` and `serve` both resolve a model's local path through the exact same call, so
they always agree on where a given model's weights actually are — whichever `HF_HOME`/
`HF_HUB_CACHE` is set to at the time.

## Verifying contract compliance

Not automated in CI (no GPU or engine binaries on the CI runner) — verify manually:

1. Start the server: `uv run gpu-node serve llama-cpp <model-name>`.
2. Send a [request](../../../configs/README.md#running-a-registry-model-locally) to the
   printed endpoint — see step 4 there for the exact command.
3. The response should validate against `common.contract.ChatCompletionResponse` — the same
   shape check `packages/common/tests/test_contract.py` runs against a captured llama.cpp
   fixture.

> **Pending:** verifying that the response reaches this server *through* the orchestrator,
> until the `orchestrator` package has an actual router.
