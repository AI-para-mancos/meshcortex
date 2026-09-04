"""Orchestrator configuration, sourced from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the orchestrator service."""

    model_config = SettingsConfigDict(env_prefix="")

    registry_path: Path = Path("configs/models.yaml")
    """Path to the shared model registry (models.yaml). Overridable via REGISTRY_PATH."""

    backend_timeout_seconds: float = 120.0
    """Timeout for backend requests. Model inference is slow, so this is generous."""


settings = Settings()
