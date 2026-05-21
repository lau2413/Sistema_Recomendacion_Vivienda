# config/settings.py
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global cargada desde variables de entorno (.env)."""

    # Selector de proveedor
    llm_provider: Literal["openai", "gemini"] = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Fuentes externas
    scraping_provider: Literal["mock", "fincaraiz", "metrocuadrado", "ciencuadras", "mixto"] = "mock"
    finca_raiz_max_resultados: int = 8
    finca_raiz_timeout_ms: int = 30000
    news_provider: Literal["mock", "google_rss", "newsapi", "mixto"] = "mock"
    news_api_key: str = ""
    news_max_resultados: int = 8

    # Otros
    max_iteraciones_relajacion: int = 3
    score_minimo_aceptable: float = 7.0
    min_alternativas: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
