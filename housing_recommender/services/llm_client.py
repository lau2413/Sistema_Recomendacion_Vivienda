# services/llm_client.py
"""
Factory centralizado para crear instancias del LLM.
Permite cambiar de proveedor (OpenAI/Gemini) modificando solo el .env.
"""

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import settings


def get_llm(temperature: float = 0):
    """
    Devuelve una instancia del LLM según el proveedor configurado en .env.

    Args:
        temperature: 0 para tareas determinísticas (extracción, evaluación),
                     valores más altos para tareas creativas.

    Returns:
        Un ChatModel de LangChain (OpenAI o Gemini).
    """
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en .env")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

    elif settings.llm_provider == "gemini":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY no está configurada en .env")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )

    else:
        raise ValueError(f"Proveedor LLM no soportado: {settings.llm_provider}")