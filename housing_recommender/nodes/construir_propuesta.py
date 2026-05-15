from __future__ import annotations

from typing import Any, Mapping

from housing_recommender.state.models import Propuesta


def construir_propuesta(estado: Any) -> dict[str, Any]:
    """Construye una propuesta compatible con el modelo Propuesta."""

    requisitos = _a_dict(_get(estado, "requisitos", {}) or {})
    propiedades = [_a_dict(propiedad) for propiedad in (_get(estado, "propiedades", []) or [])]

    candidatas = [
        propiedad
        for propiedad in propiedades
        if _cumple_requisitos(propiedad, requisitos)
    ]

    propiedades_con_score = [
        {**propiedad, "score": _calcular_score(propiedad, requisitos)}
        for propiedad in candidatas
    ]
    propiedades_con_score.sort(key=lambda propiedad: propiedad["score"], reverse=True)

    score_global = _promedio(
        [propiedad["score"] for propiedad in propiedades_con_score[:3]]
    )

    return {
        "propuesta": Propuesta(
            propiedades=propiedades_con_score[:3],
            score=score_global,
        ).model_dump()
    }


def _cumple_requisitos(propiedad: Mapping[str, Any], requisitos: Mapping[str, Any]) -> bool:
    if requisitos.get("ubicacion") and not _ubicacion_coincide(propiedad["ubicacion"], requisitos["ubicacion"]):
        return False
    if requisitos.get("precio_max") is not None and propiedad["precio"] > requisitos["precio_max"]:
        return False
    if requisitos.get("habitaciones") is not None and propiedad["habitaciones"] < requisitos["habitaciones"]:
        return False
    if requisitos.get("banos") is not None and propiedad["banos"] < requisitos["banos"]:
        return False
    if requisitos.get("parqueadero") is not None and propiedad["parqueadero"] != int(bool(requisitos["parqueadero"])):
        return False
    if requisitos.get("tipo") and propiedad["tipo"] != requisitos["tipo"]:
        return False
    if requisitos.get("area_min") is not None and propiedad["area"] < requisitos["area_min"]:
        return False
    if (
        requisitos.get("administracion_max") is not None
        and propiedad.get("administracion") is not None
        and propiedad["administracion"] > requisitos["administracion_max"]
    ):
        return False
    return True


def _calcular_score(propiedad: Mapping[str, Any], requisitos: Mapping[str, Any]) -> float:
    puntos = 0
    total = 0

    for campo in ["ubicacion", "tipo", "parqueadero"]:
        if requisitos.get(campo) is not None:
            total += 1
            if _normalizar_comparable(propiedad.get(campo)) == _normalizar_comparable(requisitos[campo]):
                puntos += 1

    for campo in ["precio_max", "habitaciones", "banos", "area_min", "administracion_max"]:
        if requisitos.get(campo) is not None:
            total += 1
            if _cumple_campo_numerico(propiedad, requisitos, campo):
                puntos += 1

    if total == 0:
        return 1.0
    return round(puntos / total, 3)


def _cumple_campo_numerico(
    propiedad: Mapping[str, Any],
    requisitos: Mapping[str, Any],
    campo: str,
) -> bool:
    if campo == "precio_max":
        return propiedad["precio"] <= requisitos[campo]
    if campo == "area_min":
        return propiedad["area"] >= requisitos[campo]
    if campo == "administracion_max":
        return propiedad.get("administracion") is None or propiedad["administracion"] <= requisitos[campo]
    return propiedad[campo] >= requisitos[campo]


def _normalizar_comparable(valor: Any) -> str:
    if isinstance(valor, bool):
        return str(int(valor))
    if isinstance(valor, int | float) and valor in (0, 1):
        return str(int(valor))
    return str(valor).lower()


def _ubicacion_coincide(ubicacion_propiedad: Any, ubicacion_requisito: Any) -> bool:
    propiedad = str(ubicacion_propiedad).lower()
    requisito = str(ubicacion_requisito).lower()
    equivalencias = {
        "sur": {"envigado", "sabaneta"},
        "norte": {"robledo"},
        "occidente": {"laureles", "belen", "robledo"},
        "centro": {"centro"},
        "poblado": {"el poblado"},
    }

    if requisito in propiedad:
        return True

    return propiedad in equivalencias.get(requisito, set())


def _promedio(valores: list[float]) -> float | None:
    if not valores:
        return None
    return round(sum(valores) / len(valores), 3)


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
