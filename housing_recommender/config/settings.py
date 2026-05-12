"""config/settings.py"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    newsapi_key: str = ""
    openai_api_key: str = ""          # alternativa LLM
    use_mock_scraping: bool = False   # True en tests
    max_paginas_scraping: int = 2
    log_level: str = "INFO"


settings = Settings()