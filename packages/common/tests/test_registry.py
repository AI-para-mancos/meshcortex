import pytest
from common.registry import load_registry

VALID_YAML = """
models:
  - name: qwen3-4b-q4
    family: qwen3
    quantization: Q4_K_M
    size_b: 4.0
    format: gguf
    node_types: [gpu]
    source_url: https://huggingface.co/Qwen/Qwen3-4B-GGUF
"""


def test_happy_path(tmp_path):
    yaml_file = tmp_path / "models.yaml"
    yaml_file.write_text(VALID_YAML)

    registry = load_registry(yaml_file)

    assert len(registry.models) == 1
    entry = registry.models[0]
    assert entry.name == "qwen3-4b-q4"
    assert entry.size_b == 4.0
    assert entry.node_types == ["gpu"]


def test_missing_file(tmp_path):
    missing = tmp_path / "does-not-exist.yaml"

    with pytest.raises(FileNotFoundError):
        load_registry(missing)


def test_malformed_yaml(tmp_path):
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("models: [")  # unclosed flow sequence — guaranteed YAML syntax error

    with pytest.raises(ValueError):
        load_registry(yaml_file)


def test_duplicate_names(tmp_path):
    yaml_file = tmp_path / "dupes.yaml"
    yaml_file.write_text("""
models:
  - name: qwen3-4b-q4
    quantization: Q4_K_M
    size_b: 4.0
    format: gguf
    node_types: [gpu]
    source_url: https://huggingface.co/Qwen/Qwen3-4B-GGUF
  - name: qwen3-4b-q4
    quantization: Q8_0
    size_b: 4.0
    format: gguf
    node_types: [gpu]
    source_url: https://huggingface.co/Qwen/Qwen3-4B-GGUF
""")

    with pytest.raises(ValueError, match="duplicate"):
        load_registry(yaml_file)


def test_invalid_node_type(tmp_path):
    yaml_file = tmp_path / "bad_node_type.yaml"
    yaml_file.write_text("""
models:
  - name: qwen3-4b-q4
    quantization: Q4_K_M
    size_b: 4.0
    format: gguf
    node_types: [quantum]
    source_url: https://huggingface.co/Qwen/Qwen3-4B-GGUF
""")

    with pytest.raises(ValueError, match="node_types"):
        load_registry(yaml_file)


def test_backends_parsed(tmp_path):
    yaml_file = tmp_path / "models.yaml"
    yaml_file.write_text("backends:\n  gpu: http://localhost:8080\nmodels: []\n")

    registry = load_registry(yaml_file)

    assert str(registry.backends["gpu"]).rstrip("/") == "http://localhost:8080"


def test_invalid_backend_node_type(tmp_path):
    yaml_file = tmp_path / "models.yaml"
    yaml_file.write_text("backends:\n  cpu: http://localhost:8080\nmodels: []\n")

    with pytest.raises(ValueError):
        load_registry(yaml_file)
