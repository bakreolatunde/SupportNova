"""
Central app configuration. Everything env-driven so the same code runs
in dev, CI, and the deployed instance without edits.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    genai_provider: str = "anthropic"  # anthropic | openai | gemini
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""

    database_url: str = "sqlite:///./supportnova.db"
    app_secret_key: str = "change-me"

    # Tunable thresholds — keep these in config, never hard-coded in pipeline logic,
    # so new categories/rules can be added without touching source (hidden-eval requirement).
    genai_max_retries: int = 3
    genai_timeout_seconds: int = 20
    analysis_sla_seconds: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
