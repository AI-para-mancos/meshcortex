# Model registry

`models.yaml` is the single shared source of truth for models used across meshcortex
nodes. Each entry follows the `ModelEntry` schema in `packages/common/src/common/registry.py`.

## Running a registry model locally

Applies to any entry with `format: gguf`.

1. Pick the entry you want to run from `models.yaml` and note its `source_url`. That
   URL always resolves to the exact `.gguf` file (not a repo root), in the form
   `https://huggingface.co/<repo>/resolve/main/<filename>` — `<repo>` and `<filename>`
   are what you pass to the download command below.

   Example (illustrative — use whatever entry you're actually testing):
   ```
   source_url: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
   ```

2. Download the file:

   ```bash
   uv tool install huggingface_hub[cli]
   hf download <repo> <filename>
   ```

   Some repos (e.g. Llama models) gate access behind accepting a license on the
   original model page — if the download 403s, accept the terms there first with the
   same Hugging Face account.

3. Run the server for your engine — see [How to run the dedicated server](#how-to-run-the-dedicated-server) below.

4. Confirm it serves the OpenAI-compatible endpoint. `<model-name>` is the entry's
   `name` field from `models.yaml` — llama.cpp ignores it, but keeping it consistent
   with the registry makes logs easier to read:
   ```powershell
   Invoke-RestMethod -Uri http://localhost:8080/v1/chat/completions -Method Post -ContentType "application/json" -Body '{"messages":[{"role":"user","content":"Hello"}]}' | ConvertTo-Json
   ```
   ```bash
   curl http://localhost:8080/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"Hello"}]}'
   ```

## How to run the dedicated server

Each backend has its own way to load a registry entry and expose it behind the
OpenAI-compatible endpoint the orchestrator expects.

### llama.cpp

A lightweight C/C++ inference engine for GGUF-quantized models. Runs on CPU and/or
GPU, which is why it's the common denominator across the team's mixed hardware.

1. Get llama.cpp: download the latest Windows CUDA release from
   https://github.com/ggml-org/llama.cpp/releases/latest — grab both the
   `llama-*-bin-win-cuda-*-x64.zip` asset and the matching
   `cudart-llama-bin-win-cu*-x64.zip` runtime, and extract them into the same folder.
   On Linux/macOS, or if you need a specific CUDA/Metal/CPU build, build from source
   following the instructions in the [llama.cpp repo](https://github.com/ggml-org/llama.cpp)
   instead of using a prebuilt release.

2. Run the server, offloading all layers to GPU.
   ```powershell
   llama-server.exe -m <model_name> --port 8080 -ngl 99 --ctx-size 4096
   ```
   ```bash
   llama-server -m <model_name> --port 8080 -ngl 99 --ctx-size 4096
   ```
   Drop `-ngl 99` (or lower it) on CPU-only machines, or if the model doesn't fit fully in VRAM.

### Ollama

Wraps llama.cpp with a model-management layer (`Modelfile` + `ollama create`) and a
background service that starts automatically — there's no separate "run the server"
step once a model is imported.

1. Install Ollama from https://ollama.com/download (Windows/macOS/Linux). It runs as
   a background service right after install.

2. Import the downloaded `.gguf` — create a file named `Modelfile` next to it:
   ```dockerfile
   FROM <local-path-to-gguf>
   ```
   then register it:
   ```powershell
   ollama create <model-name> -f Modelfile
   ```
   ```bash
   ollama create <model-name> -f Modelfile
   ```

3. It's already serving the OpenAI-compatible endpoint at
   `http://localhost:11434/v1/chat/completions` — use `<model-name>` as the request's
   `model` field.

### vLLM

Full-GPU inference engine, CUDA-only, no CPU fallback. GGUF support is experimental — vLLM's own
docs call it "highly experimental and under-optimized... might be incompatible with other
features."

> **Platform:** vLLM ships **Linux-only** wheels (`manylinux`); there is no Windows
> build. On Windows, run it inside **WSL2** (or a Linux host/container) — a native
> `pip install vllm` on Windows only finds the source distribution and won't build
> (`uv pip install --only-binary=:all: vllm` reports no `win_amd64` wheel).
>
> **VRAM:** vLLM is a full-GPU engine; for GGUF it dequantizes weights to fp16, so a
> ~2B model needs ~4 GB for weights alone, before the KV cache — it does not fit the
> team's ~4 GB VRAM floor. Use **llama.cpp or Ollama** on those machines, and run the
> vLLM path on a Linux GPU node with more headroom (8 GB or more).

1. Install (needs a CUDA-matching PyTorch build — see
   [vLLM's install docs](https://docs.vllm.ai/en/latest/getting_started/installation/index.html)
   for your CUDA version):
   ```bash
   uv pip install vllm vllm-gguf-plugin
   ```

2. Serve the downloaded `.gguf`, pointing `--tokenizer` at the *original* (non-GGUF)
   Hugging Face repo — vLLM recommends this because converting a tokenizer from the
   GGUF file itself is slow and unstable:
   ```bash
   vllm serve <local-path-to-gguf> --tokenizer <original-hf-repo> --port 8080
   ```

## Metrics

### Load time

`server`'s own startup log prints how long loading took, right before it starts listening —
no separate measurement needed.

### VRAM

`nvidia-smi --query-gpu=memory.used --format=csv` reports total VRAM in use **across the whole
GPU**. To isolate what the model actually costs:

1. Run it once **before** loading anything, as your idle baseline.
2. Load the model, then run it again once the server is up (but idle, no request in
   flight) — the difference between the two readings is the model + KV cache.

`nvidia-smi` reports in MiB. The `approx_vram_gb` field in `models.yaml` is in GB, so
divide that difference by 1024 before writing it there.

Without `nvidia-smi` (non-NVIDIA GPU, or CPU-only), use Task Manager's Performance tab instead
(GPU memory graph, or the process's working set under Details for a CPU-only run) as a
cross-platform fallback.

### Tokens/sec

Every `/v1/chat/completions` response includes a `timings` object. Use
`timings.predicted_per_second` — that's **generation** speed (how fast it produces the tokens
you read), which is what "tokens/sec" means below. Check
[## Running a registry model locally](#running-a-registry-model-locally), step 4.

## Acceptance criteria — validating a model runs correctly on your machine

- [ ] `server` starts without errors and logs a [model load time](#load-time).
- [ ] [VRAM usage](#vram) is consistent with the entry's `approx_vram_gb`, within your
      GPU's budget.
- [ ] A prompt sent to `/v1/chat/completions` returns a coherent, on-topic response.
- [ ] The response completes without an out-of-memory error or crash.
- [ ] [Tokens/sec](#tokenssec) is recorded. As a rough reference, ~5 tok/s is
      generally considered the floor for interactive chat; record the number either
      way so it's comparable across machines and candidate models.
