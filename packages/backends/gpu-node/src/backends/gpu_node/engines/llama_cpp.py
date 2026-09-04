import argparse
import subprocess
from pathlib import Path

from backends.gpu_node.download import ensure_model_downloaded
from common.registry import ModelEntry

HELP = "Serve via llama.cpp's llama-server, which runs in the foreground until stopped."

DEFAULT_PORT = 8080
# Offload all layers to GPU; lower this (or 0) on CPU-only or VRAM-constrained machines.
DEFAULT_NGL = 99
DEFAULT_CTX_SIZE = 4096
DEFAULT_LLAMA_SERVER_BIN = "llama-server"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Register llama-cpp's own `serve` flags on `parser`."""
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port llama-server listens on (default: {DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--ngl",
        type=int,
        default=DEFAULT_NGL,
        help=f"GPU layers to offload, 0 = CPU only (default: {DEFAULT_NGL}).",
    )
    parser.add_argument(
        "--ctx-size",
        type=int,
        default=DEFAULT_CTX_SIZE,
        dest="ctx_size",
        help=f"Context window size (default: {DEFAULT_CTX_SIZE}).",
    )
    parser.add_argument(
        "--llama-server-bin",
        default=DEFAULT_LLAMA_SERVER_BIN,
        dest="llama_server_bin",
        help=f"Path/name of the llama-server binary (default: {DEFAULT_LLAMA_SERVER_BIN}).",
    )


def build_command(
    model_path: Path,
    model_name: str,
    port: int = DEFAULT_PORT,
    ngl: int = DEFAULT_NGL,
    ctx_size: int = DEFAULT_CTX_SIZE,
    llama_server_bin: str = DEFAULT_LLAMA_SERVER_BIN,
) -> list[str]:
    """Assemble the `llama-server` argv for serving `model_path` under `model_name`."""
    return [
        llama_server_bin,
        "-m",
        str(model_path),
        "-a",
        model_name,
        "--port",
        str(port),
        "-ngl",
        str(ngl),
        "--ctx-size",
        str(ctx_size),
    ]


def serve(
    entry: ModelEntry,
    port: int = DEFAULT_PORT,
    ngl: int = DEFAULT_NGL,
    ctx_size: int = DEFAULT_CTX_SIZE,
    llama_server_bin: str = DEFAULT_LLAMA_SERVER_BIN,
) -> int:
    """Download `entry` if needed and run `llama-server` in the foreground.

    Returns:
        The `llama-server` process's exit code.
    """
    model_path = ensure_model_downloaded(entry)
    command = build_command(model_path, entry.name, port, ngl, ctx_size, llama_server_bin)
    return subprocess.run(command).returncode
