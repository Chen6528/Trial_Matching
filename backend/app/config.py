"""Application settings, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # App
    ingest_api_key: str = "change-me"
    cors_origins: str = "http://localhost:3000"

    # Models (overridable via env)
    extraction_model: str = "claude-haiku-4-5"
    reasoning_model: str = "claude-sonnet-4-6"
    embedding_model: str = "text-embedding-3-small"

    # Tuning knobs
    shortlist_size: int = 15
    # Prompt 2 reasoning effort (Sonnet 4.6+): low | medium | high | max.
    # Lower effort = less thinking = cheaper/faster, with some accuracy tradeoff.
    reasoning_effort: str = "low"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
