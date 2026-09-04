"""Pure model-to-backend resolution for the orchestrator."""

from common.registry import ModelRegistry


class ModelNotFoundError(Exception):
    """Raised when a requested model is not present in the registry."""

    def __init__(self, model: str) -> None:
        self.model = model
        super().__init__(f"model '{model}' not found in registry")


class BackendNotConfiguredError(Exception):
    """Raised when a model's node type has no backend URL configured."""

    def __init__(self, node_type: str) -> None:
        self.node_type = node_type
        super().__init__(f"no backend configured for node type '{node_type}'")


def resolve_backend(registry: ModelRegistry, model: str) -> str:
    """Return the backend base URL that serves ``model``.

    Resolution uses the model's first listed node type. Pure function: no I/O.

    Raises:
        ModelNotFoundError: if no registry entry matches ``model``.
        BackendNotConfiguredError: if the model's node type has no backend URL.
    """
    entry = next((m for m in registry.models if m.name == model), None)
    if entry is None:
        raise ModelNotFoundError(model)
    node_type = entry.node_types[0]
    url = registry.backends.get(node_type)
    if url is None:
        raise BackendNotConfiguredError(node_type)
    return str(url).rstrip("/")
