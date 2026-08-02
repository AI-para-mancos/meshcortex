"""Smoke test: verify that the `orchestrator` package imports correctly."""

import orchestrator


def test_orchestrator_imports() -> None:
    """The package must import without errors."""
    assert orchestrator is not None
