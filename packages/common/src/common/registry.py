from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, HttpUrl, ValidationError, field_validator, model_validator

from common.contract import AUTO_MODEL

NodeType = Literal["gpu", "edge", "router"]


class ModelEntry(BaseModel):
    name: str
    family: str | None = None
    quantization: str | None
    size_b: float
    format: Literal["gguf", "safetensors", "awq", "gptq"]
    node_types: list[NodeType]
    source_url: HttpUrl
    approx_vram_gb: float | None = None

    @field_validator("name")
    @classmethod
    def no_reserved_name(cls, value: str) -> str:
        """Reject the request-side sentinel as a catalog name.

        Case-insensitive though the wire value is exact: whoever writes `AUTO`
        expects the default behaviour, and deserves an error over a model
        nothing ever routes to.
        """
        if value.casefold() == AUTO_MODEL:
            raise ValueError(f"'{AUTO_MODEL}' is a reserved model name")
        return value


class ModelRegistry(BaseModel):
    models: list[ModelEntry]
    backends: dict[NodeType, HttpUrl] = {}

    @model_validator(mode="after")
    def no_duplicate_names(self):
        names = [m.name for m in self.models]
        if len(names) != len(set(names)):
            raise ValueError("duplicate model names in registry")
        return self


def load_registry(path: str | Path) -> ModelRegistry:
    """Load and validate the model registry from a YAML file.

    Raises:
        FileNotFoundError: if `path` does not exist.
        ValueError: if the file is not valid YAML, or the parsed content
            fails ModelRegistry validation (duplicate names, invalid
            node_types, missing required fields, etc.).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Model registry file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if raw is None:
        raise ValueError(f"Model registry file is empty: {path}")

    try:
        return ModelRegistry.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Model registry failed validation: {exc}") from exc
