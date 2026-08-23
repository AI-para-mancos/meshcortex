"""Orchestrator configuration, sourced from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the orchestrator service."""

    model_config = SettingsConfigDict(env_prefix="")

    backend_url: str = "http://localhost:8080"
    """Base URL of the inference backend to forward requests to."""

    backend_timeout_seconds: float = 120.0
    """Timeout for backend requests. Model inference is slow, so this is generous."""


settings = Settings()
