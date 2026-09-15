import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from backends.gpu_node.download import ensure_model_downloaded
from common.registry import ModelEntry

HELP = "Launch Ollama's own server on --port, import the model, and run in the foreground."

DEFAULT_OLLAMA_BIN = "ollama"
# Matches llama-cpp's default and the registry's default backend URL.
DEFAULT_PORT = 8080
# The server takes a moment to start listening -- a few attempts covers that.
CREATE_RETRIES = 3
CREATE_RETRY_INTERVAL_SECONDS = 1


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Register ollama's own `serve` flags on `parser`."""
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port ollama serve listens on (default: {DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--ollama-bin",
        default=DEFAULT_OLLAMA_BIN,
        dest="ollama_bin",
        help=f"Path/name of the ollama binary (default: {DEFAULT_OLLAMA_BIN}).",
    )


def build_modelfile(model_path: Path) -> str:
    """Return the `Modelfile` content pointing Ollama at a local GGUF file."""
    return f"FROM {model_path}\n"


def endpoint(port: int = DEFAULT_PORT) -> str:
    """Return the base URL `serve` will expose the OpenAI-compatible endpoint at."""
    return f"http://localhost:{port}"


def _create_with_retry(
    ollama_bin: str, model_name: str, modelfile_path: Path, env: dict
) -> subprocess.CompletedProcess:
    """Try `ollama create` up to `CREATE_RETRIES` times, stopping as soon as one succeeds."""
    command = [ollama_bin, "create", model_name, "-f", str(modelfile_path)]
    for attempt in range(CREATE_RETRIES):
        result = subprocess.run(command, env=env)
        if result.returncode == 0:
            return result
        if attempt < CREATE_RETRIES - 1:
            time.sleep(CREATE_RETRY_INTERVAL_SECONDS)
    return result


def serve(
    entry: ModelEntry,
    port: int = DEFAULT_PORT,
    ollama_bin: str = DEFAULT_OLLAMA_BIN,
) -> int:
    """Download `entry` if needed, then launch and import into Ollama's own server.

    Starts a second, independent `ollama serve` bound to `port` -- an existing
    system-installed Ollama instance keeps listening on its own port, untouched.

    Returns:
        A nonzero code without serving if the import fails; otherwise the server's
        exit code once stopped.
    """
    model_path = ensure_model_downloaded(entry)
    modelfile_path = model_path.parent / "Modelfile"
    modelfile_path.write_text(build_modelfile(model_path))

    env = {**os.environ, "OLLAMA_HOST": f"127.0.0.1:{port}"}
    server = subprocess.Popen([ollama_bin, "serve"], env=env)
    try:
        result = _create_with_retry(ollama_bin, entry.name, modelfile_path, env)
        if result.returncode != 0:
            return result.returncode

        print(
            f"'{entry.name}' is served by Ollama at {endpoint(port)}/v1/chat/completions "
            f'(request body: {{"model": "{entry.name}", ...}}).',
            file=sys.stderr,
        )
        return server.wait()
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait()
