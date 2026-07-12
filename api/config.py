"""Application configuration from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Absolute path (not ".env") so this is found regardless of the working
    # directory the process is launched from — a relative path here silently
    # fails to load (pydantic-settings treats a missing .env as "no overrides",
    # not an error), which previously caused ARCHX_MODEL_PATH to be ignored
    # and the API to fall back to mock inference without any visible error.
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    archx_model_path: str | None = None
    archx_mock_inference: bool | None = None

    @field_validator("archx_mock_inference", mode="before")
    @classmethod
    def _empty_string_as_unset(cls, value: object) -> object:
        """A `.env` line like `ARCHX_MOCK_INFERENCE=` (no value) is the common
        way to leave a setting unset — pydantic-settings otherwise fails to
        parse "" as a bool. Treat blank as None (falls back to the
        archx_model_path-based default in use_mock_inference below)."""
        if isinstance(value, str) and value.strip() == "":
            return None
        return value
    cors_origins: list[str] = ["http://localhost:3000"]
    demo_projects_dir: Path = PROJECT_ROOT / "demo_projects"
    archx_feedback_path: Path = PROJECT_ROOT / "feedback" / "collected_feedback.jsonl"
    archx_clone_dir: Path = PROJECT_ROOT / "tmp" / "clones"
    archx_clone_timeout: int = 120
    archx_clone_depth: int = 500

    @property
    def clone_dir(self) -> Path:
        return self.archx_clone_dir

    @property
    def clone_timeout(self) -> int:
        return self.archx_clone_timeout

    @property
    def clone_depth(self) -> int:
        return self.archx_clone_depth

    @property
    def use_mock_inference(self) -> bool:
        if self.archx_mock_inference is not None:
            return self.archx_mock_inference
        return self.archx_model_path is None


settings = Settings()
