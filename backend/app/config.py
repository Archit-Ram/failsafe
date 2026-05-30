"""Settings loaded from .env / environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "sqlite:///./failsafe.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 720

    ml_model_path: str = str(REPO_ROOT / "ml" / "models" / "xgb_failsafe.json")
    ml_pipeline_path: str = str(REPO_ROOT / "ml" / "models" / "preprocessor.joblib")
    ml_background_path: str = str(REPO_ROOT / "ml" / "models" / "shap_background.npy")
    ml_metadata_path: str = str(REPO_ROOT / "ml" / "models" / "metadata.json")

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
