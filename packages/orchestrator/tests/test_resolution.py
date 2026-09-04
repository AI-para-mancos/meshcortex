"""Unit tests for the pure model-to-backend resolution function."""

import pytest
from common.registry import ModelRegistry
from orchestrator.resolution import (
    BackendNotConfiguredError,
    ModelNotFoundError,
    resolve_backend,
)


def _registry(**overrides) -> ModelRegistry:
    data = {
        "backends": {"gpu": "http://gpu.test", "edge": "http://edge.test"},
        "models": [
            {
                "name": "m-gpu",
                "quantization": "Q4_K_M",
                "size_b": 1.0,
                "format": "gguf",
                "node_types": ["gpu", "edge"],
                "source_url": "https://example.test/m.gguf",
            }
        ],
    }
    data.update(overrides)
    return ModelRegistry.model_validate(data)


def test_resolves_to_first_node_type() -> None:
    assert resolve_backend(_registry(), "m-gpu") == "http://gpu.test"


def test_unknown_model_raises() -> None:
    with pytest.raises(ModelNotFoundError):
        resolve_backend(_registry(), "missing")


def test_missing_backend_raises() -> None:
    with pytest.raises(BackendNotConfiguredError):
        resolve_backend(_registry(backends={}), "m-gpu")
