from __future__ import annotations

import json
from typing import Any

import httpx

from housing_recommender.config.settings import settings


def generar_json_estructurado(prompt: str) -> dict[str, Any] | None:
    """Calls the configured LLM and returns a JSON object, or None on fallback."""

    try:
        if settings.llm_provider == "openai":
            return _generar_con_openai(prompt)
        if settings.llm_provider == "gemini":
            return _generar_con_gemini(prompt)
        return None
    except (httpx.HTTPError, KeyError, IndexError, TypeError):
        return None


def _generar_con_openai(prompt: str) -> dict[str, Any] | None:
    if not settings.openai_api_key:
        return None

    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _parse_json(content)


def _generar_con_gemini(prompt: str) -> dict[str, Any] | None:
    if not settings.google_api_key:
        return None

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    response = httpx.post(
        url,
        params={"key": settings.google_api_key},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_json(content)


def _parse_json(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None