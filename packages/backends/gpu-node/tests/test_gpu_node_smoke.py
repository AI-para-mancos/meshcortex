"""Smoke test mínimo: verifica que el paquete `backends.gpu_node` se importa."""

import backends.gpu_node


def test_gpu_node_importa() -> None:
    """El paquete debe importarse sin errores."""
    assert backends.gpu_node is not None
