from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_recommender.services.noticias_client import obtener_noticias
from housing_recommender.state.models import Noticia


def agente_noticias(estado: Any) -> dict[str, Any]:
    """Nodo Persona 2: consulta contexto y escribe solo noticias."""

    ubicaciones = _obtener_ubicaciones(estado)
    noticias_crudas, diagnostico = obtener_noticias(
        ubicaciones,
        incluir_diagnostico=True,
    )
    noticias = [
        Noticia(**noticia).model_dump()
        for noticia in noticias_crudas
    ]
    return {"noticias": noticias, "diagnostico_noticias": diagnostico}


def _obtener_ubicaciones(estado: Any) -> list[str]:
    propiedades = _get(estado, "propiedades", []) or []
    ubicaciones = []

    for propiedad in propiedades:
        ubicacion = _get(propiedad, "ubicacion")
        if ubicacion and ubicacion not in ubicaciones:
            ubicaciones.append(ubicacion)

    requisitos = _get(estado, "requisitos")
    ubicacion_requisito = _get(requisitos, "ubicacion") if requisitos else None
    if ubicacion_requisito and ubicacion_requisito not in ubicaciones:
        ubicaciones.append(ubicacion_requisito)

    return ubicaciones


def _get(valor: Any, campo: str, default: Any = None) -> Any:
    if isinstance(valor, Mapping):
        return valor.get(campo, default)
    return getattr(valor, campo, default)
