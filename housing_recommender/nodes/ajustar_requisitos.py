"""
nodes/ajustar_requisitos.py  — Nodo ①
Responsabilidad: tomar el texto libre del usuario y estructurarlo
en un objeto CriteriosUsuario.
Produce: {"criterios_actuales": ...}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from config.settings import settings
from services.llm_client import llamar_llm
from services.requisitos_parser import extraer_criterios_desde_texto
from state.models import CriteriosUsuario, EstadoSistema


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "ajustar_requisitos.txt"


def _cargar_prompt() -> str:
    try:
        with PROMPT_PATH.open(encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return (
            "Eres un asistente inmobiliario. Extrae los criterios de búsqueda "
            "de vivienda del siguiente texto y devuelve SOLO un JSON válido con "
            "los campos: ciudad, tipo_inmueble, precio_min, precio_max, area_min, "
            "area_max, habitaciones_min, barrios_preferidos (lista), modalidad. "
            "Si no se menciona un campo, usa null. No incluyas explicaciones."
        )


async def ajustar_requisitos(estado: EstadoSistema) -> dict:
    """
    Nodo LangGraph. Recibe el estado completo, devuelve solo los campos que modifica.
    """
    texto = estado.texto_libre_usuario or "Busco apartamento en Medellín"

    if settings.gemini_api_key or settings.openai_api_key:
        sistema = _cargar_prompt()
        respuesta = await llamar_llm(
            sistema=sistema,
            usuario=f"Texto del usuario: {texto}",
        )
        criterios_dict = _extraer_json(respuesta)
    else:
        criterios_dict = extraer_criterios_desde_texto(texto)

    base = estado.criterios_actuales.model_dump()
    criterios_dict = {k: v for k, v in criterios_dict.items() if v is not None}
    criterios = CriteriosUsuario(**(base | criterios_dict))

    return {"criterios_actuales": criterios}


def _extraer_json(texto: str) -> dict:
    """Extrae el primer bloque JSON de una cadena."""
    # Intentar parsear directo
    try:
        return json.loads(texto.strip())
    except json.JSONDecodeError:
        pass

    # Buscar bloque ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Buscar primer { ... } en el texto
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback: criterios vacíos, la ciudad por defecto aplica
    return {}
