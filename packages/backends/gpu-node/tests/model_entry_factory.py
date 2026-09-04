from common.registry import ModelEntry

DEFAULT_SOURCE_URL = "https://huggingface.co/org/repo/resolve/main/model.gguf"
DEFAULT_MODEL_ENTRY_FIELDS = {
    "name": "qwen3-1.7b-q4",
    "family": "qwen3",
    "quantization": "Q4_K_M",
    "size_b": 1.7,
    "format": "gguf",
    "node_types": ["gpu"],
    "source_url": DEFAULT_SOURCE_URL,
    "approx_vram_gb": 1.5,
}


def make_model_entry(**overrides) -> ModelEntry:
    """Build a valid `ModelEntry` for tests; `overrides` replace any default field."""
    return ModelEntry.model_validate({**DEFAULT_MODEL_ENTRY_FIELDS, **overrides})
