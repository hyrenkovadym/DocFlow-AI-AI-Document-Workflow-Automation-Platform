from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = API_DIR.parents[1] if len(API_DIR.parents) > 1 else API_DIR


class Settings(BaseSettings):
    project_name: str = "DocFlow AI"
    environment: str = "development"
    api_v1_prefix: str = "/api"

    database_url: str = "postgresql+psycopg2://docflow:docflow@localhost:5432/docflow"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "replace-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    allowed_file_types: str = "pdf,docx,txt"

    ai_provider: str = "mock"
    ai_min_confidence: float = 0.7
    openai_api_key: str | None = None
    openai_api_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(API_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_file_extensions(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_file_types.split(",") if item.strip()}

    @property
    def resolved_upload_dir(self) -> Path:
        return Path(self.upload_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
