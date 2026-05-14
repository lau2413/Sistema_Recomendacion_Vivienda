# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global cargada desde variables de entorno (.env)."""

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    max_iteraciones_relajacion: int = 3
    score_minimo_aceptable: float = 7.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Instancia única que se importa desde el resto del proyecto
settings = Settings()