"""
services/llm_client.py
Wrapper mínimo para llamar al LLM. Soporta Gemini (primario) y OpenAI (fallback).
"""
from __future__ import annotations

import httpx
from config.settings import settings


async def llamar_llm(sistema: str, usuario: str, max_tokens: int = 1000) -> str:
    """Llama al LLM configurado y devuelve el texto de respuesta."""
    if settings.gemini_api_key:
        return await _llamar_gemini(sistema, usuario, max_tokens)
    elif settings.openai_api_key:
        return await _llamar_openai(sistema, usuario, max_tokens)
    else:
        raise RuntimeError("Configura GEMINI_API_KEY u OPENAI_API_KEY en .env")


async def _llamar_gemini(sistema: str, usuario: str, max_tokens: int) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": sistema}]},
        "contents": [{"parts": [{"text": usuario}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


async def _llamar_openai(sistema: str, usuario: str, max_tokens: int) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    payload = {
        "model": "gpt-4o-mini",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]