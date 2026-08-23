import argparse
import warnings
from pathlib import Path

from backends.gpu_node.download import ensure_model_downloaded
from backends.gpu_node.engines import ENGINES
from common.registry import ModelEntry, load_registry

DEFAULT_REGISTRY_PATH = Path("configs/models.yaml")

# Namespace keys that belong to `serve` itself, not to the selected engine's own flags.
_SERVE_OWN_ARGS = {"command", "engine", "model_name", "registry"}


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("model_name", help="Model 'name' field from the registry.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help=f"Path to the model registry YAML (default: {DEFAULT_REGISTRY_PATH}).",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gpu-node")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser(
        "download",
        help="Download a registry model's weights, if not already cached.",
        description=(
            "Download a registry model's weights via huggingface_hub, if not already "
            "cached. Where the weights land is huggingface_hub's own decision -- set "
            "HF_HOME/HF_HUB_CACHE to relocate it."
        ),
    )
    _add_common_arguments(download_parser)

    serve_parser = subparsers.add_parser(
        "serve",
        help="Download (if needed) and serve a registry model with a given engine.",
        description=(
            "Download (if needed) and serve a registry model. Pick an engine -- each one "
            "exposes its own flags (see `gpu-node serve <engine> --help`)."
        ),
    )
    engine_subparsers = serve_parser.add_subparsers(dest="engine", required=True)

    # Each engine owns its own flags -- adding a new engine means adding a module with
    # `HELP`/`add_arguments`/`serve` and one entry in `ENGINES`.
    for name, engine_module in ENGINES.items():
        engine_parser = engine_subparsers.add_parser(
            name, help=engine_module.HELP, description=engine_module.HELP
        )
        _add_common_arguments(engine_parser)
        engine_module.add_arguments(engine_parser)

    return parser


def _resolve_entry(registry_path: Path, model_name: str) -> ModelEntry:
    """Look up `model_name` in the registry at `registry_path`.

    Raises:
        ValueError: if `model_name` isn't in the registry.
    """
    registry = load_registry(registry_path)
    entry = next((model for model in registry.models if model.name == model_name), None)
    if entry is None:
        raise ValueError(f"Model '{model_name}' not found in {registry_path}")

    if "gpu" not in entry.node_types:
        warnings.warn(
            f"'{entry.name}' is not tagged with node_types: [gpu] in the registry.",
            stacklevel=2,
        )

    return entry


def _download(args: argparse.Namespace) -> None:
    entry = _resolve_entry(args.registry, args.model_name)
    model_path = ensure_model_downloaded(entry)
    print(f"[INFO] Model downloaded on '{model_path}'.")


def _serve(args: argparse.Namespace) -> int:
    entry = _resolve_entry(args.registry, args.model_name)
    engine_module = ENGINES[args.engine]
    kwargs = {key: value for key, value in vars(args).items() if key not in _SERVE_OWN_ARGS}
    return engine_module.serve(entry, **kwargs)


def run(argv: list[str] | None = None) -> int:
    """Console-script entry point: parse `argv` and dispatch to `download`/`serve`."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        _download(args)
        return 0
    return _serve(args)
