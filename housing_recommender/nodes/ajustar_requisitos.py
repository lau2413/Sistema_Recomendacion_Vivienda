from __future__ import annotations

from typing import Any, Mapping

from housing_recommender.services.requisitos_parser import extraer_requisitos_desde_texto


def ajustar_requisitos(estado: Any) -> dict[str, Any]:
    """Nodo Persona 2: interpreta textoUsuario y escribe solo requisitos."""

    requisitos = _a_dict(_get(estado, "requisitos", {}) or {})
    texto_usuario = _get(estado, "textoUsuario", "")

    if texto_usuario:
        requisitos.update(extraer_requisitos_desde_texto(str(texto_usuario)))

    return {"requisitos": requisitos}


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
