"""Smoke test: verify that the `backends.gpu_node` package imports correctly."""

import backends.gpu_node


def test_gpu_node_imports() -> None:
    """The package must import without errors."""
    assert backends.gpu_node is not None
