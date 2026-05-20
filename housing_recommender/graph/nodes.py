"""Nodos conectados por el grafo de LangGraph."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_recommender.nodes.agente_noticias import agente_noticias
from housing_recommender.nodes.agente_relajacion import agente_relajacion
from housing_recommender.nodes.ajustar_requisitos import ajustar_requisitos
from housing_recommender.nodes.construir_propuesta import construir_propuesta
from housing_recommender.nodes.evaluador import evaluador
from housing_recommender.nodes.presentar_resultado import presentar_resultado
from housing_recommender.nodes.propiedades_scraping import propiedades_scraping


ZONAS_MEDELLIN = [
    "El Poblado",
    "Laureles",
    "Envigado",
    "Sabaneta",
    "Belen",
    "Robledo",
    "Centro",
]

ZONAS_POR_CONTEXTO = {
    "sur": ["Envigado", "Sabaneta", "El Poblado"],
    "norte": ["Robledo"],
    "occidente": ["Laureles", "Belen", "Robledo"],
    "centro": ["Centro"],
    "poblado": ["El Poblado"],
}


def zonas_contexto(estado: Any) -> dict[str, Any]:
    """Deriva zonas de busqueda desde requisitos y deja diagnostico trazable."""

    requisitos = _a_dict(_get(estado, "requisitos", {}) or {})
    ubicacion = str(requisitos.get("ubicacion") or "").strip()
    clave = ubicacion.lower()

    if not ubicacion:
        zonas_analizadas = ZONAS_MEDELLIN[:5]
        zonas_seleccionadas = zonas_analizadas[:3]
        diagnostico_zonas = (
            "No se especifico ubicacion; se usaron zonas generales de Medellin "
            "para ampliar la busqueda inicial."
        )
    else:
        zonas_analizadas = ZONAS_POR_CONTEXTO.get(clave, [ubicacion])
        zonas_seleccionadas = zonas_analizadas[:3]
        diagnostico_zonas = (
            f"Se derivaron zonas de busqueda desde la ubicacion solicitada: {ubicacion}."
        )

    diagnostico = _combinar_diagnosticos(_get(estado, "diagnostico"), diagnostico_zonas)
    return {
        "zonas_analizadas": zonas_analizadas,
        "zonas_seleccionadas": zonas_seleccionadas,
        "diagnostico": diagnostico,
    }


def _get(valor: Any, campo: str, default: Any = None) -> Any:
    if isinstance(valor, Mapping):
        return valor.get(campo, default)
    return getattr(valor, campo, default)


def _a_dict(valor: Any) -> dict[str, Any]:
    if isinstance(valor, Mapping):
        return dict(valor)
    if hasattr(valor, "model_dump"):
        return valor.model_dump(exclude_none=True)
    if hasattr(valor, "dict"):
        return valor.dict(exclude_none=True)
    return {}


def _combinar_diagnosticos(actual: Any, nuevo: str) -> str:
    actual_limpio = str(actual or "").strip()
    if not actual_limpio:
        return nuevo
    if nuevo in actual_limpio:
        return actual_limpio
    return f"{actual_limpio}\n{nuevo}"
