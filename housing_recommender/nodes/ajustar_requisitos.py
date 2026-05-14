from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from housing_recommender.services.llm_client import generar_json_estructurado
from housing_recommender.services.requisitos_parser import extraer_requisitos_desde_texto

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "ajustar_requisitos.txt"


def ajustar_requisitos(estado: Any) -> dict[str, Any]:
    """Nodo Persona 2: interpreta textoUsuario y escribe solo requisitos."""

    requisitos = _a_dict(_get(estado, "requisitos", {}) or {})
    texto_usuario = _get(estado, "textoUsuario", "")

    if texto_usuario:
        extraidos = _extraer_con_llm(str(texto_usuario), requisitos)
        if extraidos is None:
            extraidos = extraer_requisitos_desde_texto(str(texto_usuario))
        requisitos.update(_sin_nulos(extraidos))

    return {"requisitos": requisitos}


def _extraer_con_llm(texto_usuario: str, requisitos_previos: Mapping[str, Any]) -> dict[str, Any] | None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
        texto_usuario=texto_usuario,
        requisitos_previos=json.dumps(dict(requisitos_previos), ensure_ascii=False),
    )
    return generar_json_estructurado(prompt)


def _sin_nulos(valores: Mapping[str, Any]) -> dict[str, Any]:
    return {clave: valor for clave, valor in valores.items() if valor is not None}


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
