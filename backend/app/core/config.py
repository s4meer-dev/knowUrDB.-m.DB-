from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "knowUrDB (m.DB)"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    FRONTEND_URL: str = "http://localhost:5173"

    # MongoDB Native Configuration
    MONGODB_URI: str = Field(
        default="mongodb://127.0.0.1:27017",
        description="MongoDB connection URI",
    )
    MONGODB_DATABASE: str = Field(
        default="knowurdb",
        description="Primary MongoDB database name",
    )
    MONGODB_MAX_POOL_SIZE: int = Field(
        default=50,
        description="Maximum MongoDB connection pool size",
    )
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = Field(
        default=3000,
        description="Server selection timeout in milliseconds",
    )

    # AI / LLM Configuration
    GEMINI_API_KEY: str | None = Field(
        default=None, validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY")
    )
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Query & Ingestion Performance Safeguards
    MAX_QUERY_LIMIT: int = 500
    QUERY_TIMEOUT_MS: int = 10000
    MAX_UPLOAD_SIZE_MB: int = 100

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
