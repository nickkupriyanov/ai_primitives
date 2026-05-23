from functools import lru_cache
from os import getenv
from typing import Literal

from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is in requirements.
    load_dotenv = None


class Settings(BaseModel):
    app_name: str = "ai-backend"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30
    llm_max_retries: int = Field(default=3, ge=1)
    log_level: str = "INFO"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )


def _csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    if load_dotenv is not None:
        load_dotenv()

    return Settings(
        app_name=getenv("APP_NAME", "ai-backend"),
        app_version=getenv("APP_VERSION", "0.1.0"),
        app_env=getenv("APP_ENV", "development"),  # type: ignore[arg-type]
        host=getenv("HOST", "0.0.0.0"),
        port=int(getenv("PORT", "8000")),
        openai_api_key=getenv("OPENAI_API_KEY") or getenv("AI_API_KEY"),
        openai_base_url=getenv("OPENAI_BASE_URL") or getenv("BASE_URL"),
        openai_model=getenv("OPENAI_MODEL", "gpt-4o-mini"),
        llm_timeout_seconds=float(getenv("LLM_TIMEOUT_SECONDS", "30")),
        llm_max_retries=int(getenv("LLM_MAX_RETRIES", "3")),
        log_level=getenv("LOG_LEVEL", "INFO"),
        cors_origins=_csv(
            getenv("CORS_ORIGINS"),
            ["http://localhost:3000", "http://localhost:5173"],
        ),
    )
