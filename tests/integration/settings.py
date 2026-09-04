from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class IntegrationSettings(BaseSettings):
    """Everything the integration suite reads from the environment."""

    model_config = SettingsConfigDict(env_prefix="INTEGRATION_")

    model: str
    """Registry name of the model under test.

    Deliberately has no default. The right value depends on what the local stack is
    actually serving, and a default would silently point the suite at the wrong model
    and report a mismatch that looks like a backend bug.
    """

    orchestrator_url: str = "http://localhost:8000"
    """Base URL of the gateway under test."""

    timeout_seconds: float = 120.0
    """Per-request timeout. CPU-only inference is far slower than GPU, so CI raises it."""

    @field_validator("orchestrator_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        """Paths are joined onto this, so a trailing slash would produce a double slash."""
        return value.rstrip("/")
