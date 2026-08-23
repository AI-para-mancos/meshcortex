import pytest
import yaml
from model_entry_factory import DEFAULT_MODEL_ENTRY_FIELDS

_REGISTRY_YAML = yaml.safe_dump({"models": [DEFAULT_MODEL_ENTRY_FIELDS]})
_REGISTRY_YAML_NON_GPU = yaml.safe_dump(
    {"models": [{**DEFAULT_MODEL_ENTRY_FIELDS, "node_types": ["edge"]}]}
)


@pytest.fixture
def registry_path(tmp_path):
    """A `models.yaml` registry containing one gpu-tagged entry: `qwen3-1.7b-q4`."""
    path = tmp_path / "models.yaml"
    path.write_text(_REGISTRY_YAML)
    return path


@pytest.fixture
def non_gpu_registry_path(tmp_path):
    """Same registry as `registry_path`, but `qwen3-1.7b-q4` is tagged `node_types: [edge]`."""
    path = tmp_path / "models.yaml"
    path.write_text(_REGISTRY_YAML_NON_GPU)
    return path
