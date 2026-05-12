"""
services/noticias_client.py
Busca noticias recientes sobre barrios / zonas de la ciudad.
Estrategia: DuckDuckGo Instant Answer API (sin key) como primario,
NewsAPI como alternativa si se configura NEWSAPI_KEY en .env.
"""
from __future__ import annotations

import os
from urllib.parse import quote_plus

import httpx

from config.settings import settings

DDGO_URL = "https://api.duckduckgo.com/"
NEWSAPI_URL = "https://newsapi.org/v2/everything"


async def _buscar_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(DDGO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    resultados = []
    for item in data.get("RelatedTopics", [])[:max_results]:
        if "Text" in item:
            resultados.append({
                "titulo": item.get("Text", "")[:120],
                "url": item.get("FirstURL", ""),
                "fuente": "duckduckgo",
            })
    return resultados


async def _buscar_newsapi(query: str, max_results: int = 5) -> list[dict]:
    api_key = settings.newsapi_key
    if not api_key:
        return []

    params = {
        "q": query,
        "language": "es",
        "sortBy": "relevancy",
        "pageSize": max_results,
        "apiKey": api_key,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(NEWSAPI_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "titulo": a.get("title", ""),
            "descripcion": a.get("description", ""),
            "url": a.get("url", ""),
            "fecha": a.get("publishedAt", ""),
            "fuente": a.get("source", {}).get("name", "newsapi"),
        }
        for a in data.get("articles", [])
    ]


async def buscar_noticias_zona(
    ciudad: str,
    barrios: list[str],
    max_por_barrio: int = 3,
) -> list[dict[str, str]]:
    """
    Busca noticias recientes sobre cada barrio + ciudad.
    Devuelve lista de dicts {titulo, url, fuente, barrio}.
    """
    todas: list[dict] = []
    targets = barrios if barrios else [ciudad]

    for zona in targets[:4]:  # máx 4 zonas para no saturar
        query = f"{zona} {ciudad} seguridad valorización vivienda"
        noticias: list[dict] = []

        # Intentar NewsAPI primero (más rico), luego DuckDuckGo
        try:
            noticias = await _buscar_newsapi(query, max_por_barrio)
        except Exception:
            pass

        if not noticias:
            try:
                noticias = await _buscar_duckduckgo(query, max_por_barrio)
            except Exception:
                pass

        for n in noticias:
            n["barrio"] = zona
        todas.extend(noticias)

    return todas


# ─── Mock para tests ──────────────────────────────────────────────────────────

def mock_noticias(barrios: list[str]) -> list[dict[str, str]]:
    """Noticias falsas para tests sin red."""
    return [
        {
            "titulo": f"Valorización récord en {b} durante 2024",
            "url": f"https://ejemplo.com/noticia-{i}",
            "fuente": "mock",
            "barrio": b,
        }
        for i, b in enumerate(barrios or ["El Poblado"])
    ]