"""Application configuration from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    archx_model_path: str | None = None
    archx_mock_inference: bool | None = None
    cors_origins: list[str] = ["http://localhost:3000"]
    demo_projects_dir: Path = PROJECT_ROOT / "demo_projects"
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
