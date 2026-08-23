from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "knowUrDB-backend"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    FRONTEND_URL: str = "http://localhost:5173"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.1-pro"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
