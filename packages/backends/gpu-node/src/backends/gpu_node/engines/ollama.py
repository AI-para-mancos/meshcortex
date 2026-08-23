import argparse
import subprocess
import sys
from pathlib import Path

from backends.gpu_node.download import ensure_model_downloaded
from common.registry import ModelEntry

HELP = (
    "Import into Ollama's already-running background service and return -- there is no "
    "per-model process to hold open."
)

DEFAULT_OLLAMA_BIN = "ollama"
DEFAULT_ENDPOINT = "http://localhost:11434/v1/chat/completions"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Register ollama's own `serve` flags on `parser`."""
    parser.add_argument(
        "--ollama-bin",
        default=DEFAULT_OLLAMA_BIN,
        dest="ollama_bin",
        help=f"Path/name of the ollama binary (default: {DEFAULT_OLLAMA_BIN}).",
    )


def build_modelfile(model_path: Path) -> str:
    """Return the `Modelfile` content pointing Ollama at a local GGUF file."""
    return f"FROM {model_path}\n"


def serve(entry: ModelEntry, ollama_bin: str = DEFAULT_OLLAMA_BIN) -> int:
    """Download `entry` if needed, import it into Ollama, and report where it's served.

    The `Modelfile` is only a one-time pointer consumed by `ollama create` -- it's
    written next to the downloaded weights (not left anywhere in the repo) and isn't
    cleaned up afterward.

    Returns:
        The `ollama create` process's exit code (`0` on success).
    """
    model_path = ensure_model_downloaded(entry)
    modelfile_path = model_path.parent / "Modelfile"
    modelfile_path.write_text(build_modelfile(model_path))

    result = subprocess.run([ollama_bin, "create", entry.name, "-f", str(modelfile_path)])

    if result.returncode != 0:
        return result.returncode

    print(
        f"'{entry.name}' is served by Ollama at {DEFAULT_ENDPOINT} "
        f'(request body: {{"model": "{entry.name}", ...}}).',
        file=sys.stderr,
    )
    return 0
