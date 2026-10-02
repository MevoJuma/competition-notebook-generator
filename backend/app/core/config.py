from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings managed through Pydantic v2."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core Application
    PROJECT_NAME: str = "AI Competition Analysis & Notebook Generation Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev_secret_key_change_in_production"

    # Server Binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/platform.db"
    DATABASE_ECHO: bool = False

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_TIMEOUT_SECONDS: int = 1800

    # Storage Paths
    STORAGE_TYPE: str = "local"
    STORAGE_ROOT: str = "./storage"
    STORAGE_UPLOAD_DIR: str = "./storage/uploads"
    STORAGE_GENERATED_DIR: str = "./storage/generated"

    # Ingestion & Security Guardrails
    MAX_UPLOAD_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB
    MAX_TOTAL_ARCHIVE_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
    MAX_ZIP_COMPRESSION_RATIO: int = 10  # Protection against Zip-Bombs

    # LLM Engine (OpenAI-compatible)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    LLM_MODEL: str = "gemini-2.0-flash"
    LLM_TEMPERATURE: float = 0.2
    LLM_REQUEST_TIMEOUT_SECONDS: int = 60

    @property
    def upload_path(self) -> Path:
        """Resolved path to storage uploads directory."""
        path = Path(self.STORAGE_UPLOAD_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def generated_path(self) -> Path:
        """Resolved path to storage generated artifacts directory."""
        path = Path(self.STORAGE_GENERATED_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
