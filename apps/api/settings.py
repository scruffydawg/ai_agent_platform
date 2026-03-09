from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_name: str = Field(default="AI Agent Platform API", alias="APP_NAME")
    auth_enabled: bool = Field(default=True, alias="AUTH_ENABLED")
    operator_api_key: str = Field(default="", alias="AGENT_API_KEY")

    llm_base_url: str = Field(default="http://localhost:11434", alias="LLM_BASE_URL")
    default_model: str = Field(default="qwen2.5-coder:14b", alias="DEFAULT_MODEL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    searxng_url: str = Field(default="http://localhost:8080", alias="SEARXNG_URL")
    postgres_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/agent_db",
        alias="POSTGRES_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    storage_root: str = Field(default="/home/scruffydawg/gemini_workspace", alias="DEFAULT_STORAGE_ROOT")
    project_root: str = Field(default="/home/scruffydawg/gemini_workspace/ai_agent_platform", alias="PROJECT_ROOT")

@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
