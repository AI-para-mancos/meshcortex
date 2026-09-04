from pathlib import Path
from urllib.parse import urlparse

from common.registry import ModelEntry
from huggingface_hub import hf_hub_download


def parse_hf_source_url(source_url: str) -> tuple[str, str]:
    """Split a Hugging Face `.../<repo>/resolve/<revision>/<filename>` URL.

    Returns:
        A `(repo_id, filename)` tuple.

    Raises:
        ValueError: if `source_url` doesn't contain a `/resolve/<revision>/` segment.
    """
    path = urlparse(source_url).path.lstrip("/")
    repo_id, separator, rest = path.partition("/resolve/")
    _, _, filename = rest.partition("/")

    if not separator or not repo_id or not filename:
        raise ValueError(
            f"Not a Hugging Face file URL (expected '.../resolve/<revision>/<filename>'): "
            f"{source_url}"
        )

    return repo_id, filename


def ensure_model_downloaded(entry: ModelEntry) -> Path:
    """Return the local path to `entry`'s weights, downloading them if not already cached.

    Where the weights land is entirely huggingface_hub's own decision (its default cache,
    normally outside the repo) -- auth, cache location, transfer acceleration, and mirror
    endpoint are all left to its environment variables (HF_TOKEN, HF_HOME/HF_HUB_CACHE,
    HF_HUB_ENABLE_HF_TRANSFER, HF_ENDPOINT) rather than exposed as gpu-node flags. Every
    caller (the `download` CLI command and both serving engines) resolves through this
    same function, so they always agree on where a given model's file actually is.

    Raises:
        ValueError: if `entry.format` isn't `gguf` (the only format supported so far),
            or `entry.source_url` isn't a recognizable Hugging Face file URL.
    """
    if entry.format != "gguf":
        raise ValueError(f"Only the 'gguf' format is supported for download, got: {entry.format}")

    repo_id, filename = parse_hf_source_url(str(entry.source_url))

    local_path = hf_hub_download(repo_id=repo_id, filename=filename)
    return Path(local_path)
