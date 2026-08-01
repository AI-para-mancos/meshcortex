"""Smoke test mínimo: verifica que el paquete `orchestrator` se importa."""

import orchestrator


def test_orchestrator_importa() -> None:
    """El paquete debe importarse sin errores."""
    assert orchestrator is not None
