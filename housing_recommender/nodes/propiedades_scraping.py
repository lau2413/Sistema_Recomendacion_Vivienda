from __future__ import annotations

from typing import Any, Mapping

from housing_recommender.services.scraping_client import obtener_propiedades


def propiedades_scraping(estado: Any) -> dict[str, Any]:
    """Nodo Persona 2: busca viviendas y escribe solo propiedades."""

    requisitos = _a_dict(_get(estado, "requisitos", {}) or {})
    propiedades = obtener_propiedades(requisitos)
    return {"propiedades": propiedades}


def _get(estado: Any, campo: str, default: Any = None) -> Any:
    if isinstance(estado, Mapping):
        return estado.get(campo, default)
    return getattr(estado, campo, default)


def _a_dict(valor: Any) -> dict[str, Any]:
    if isinstance(valor, Mapping):
        return dict(valor)
    if hasattr(valor, "model_dump"):
        return valor.model_dump(exclude_none=True)
    if hasattr(valor, "dict"):
        return valor.dict(exclude_none=True)
    return {}
