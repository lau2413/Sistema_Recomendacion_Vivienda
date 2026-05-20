"""Nodo evaluador de la propuesta inmobiliaria."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_recommender.state.models import Evaluacion


class EvaluadorResultados:
    """Evalua propuesta, propiedades disponibles y requisitos actuales."""

    def __init__(self, min_propiedades: int = 1, score_minimo: float = 0.6) -> None:
        self.min_propiedades = min_propiedades
        self.score_minimo = score_minimo

    def evaluar(self, estado: Any) -> dict[str, Any]:
        self._diagnostico_actual = _get(estado, "diagnostico")
        propuesta = _a_dict(_get(estado, "propuesta", {}) or {})
        requisitos = _a_dict(_get(estado, "requisitos", {}) or {})
        propiedades = [_a_dict(prop) for prop in (_get(estado, "propiedades", []) or [])]
        propiedades_propuesta = [
            _a_dict(prop) for prop in (propuesta.get("propiedades") or [])
        ]

        if not propiedades:
            return self._resultado(
                es_aceptable=False,
                score=0.0,
                razon="No se encontraron propiedades para evaluar.",
                recomendacion="precio_max",
                diagnostico="Fallo de busqueda: el scraper no devolvio propiedades.",
            )

        if not propiedades_propuesta:
            recomendacion = self._recomendar_relajacion(propiedades, requisitos)
            return self._resultado(
                es_aceptable=False,
                score=0.0,
                razon=(
                    "Hay propiedades disponibles, pero ninguna cumple los requisitos "
                    "actuales para construir una propuesta."
                ),
                recomendacion=recomendacion,
                diagnostico=(
                    "Fallo de propuesta: construir_propuesta no encontro candidatas "
                    "compatibles con requisitos."
                ),
            )

        scores = [
            _score_propiedad(propiedad, requisitos)
            for propiedad in propiedades_propuesta
        ]
        score_promedio = _promedio(scores)
        score_propuesta = propuesta.get("score")
        if score_propuesta is not None:
            score_promedio = float(score_propuesta)

        cantidad_suficiente = len(propiedades_propuesta) >= self.min_propiedades
        es_aceptable = cantidad_suficiente and score_promedio >= self.score_minimo
        recomendacion = None if es_aceptable else self._recomendar_relajacion(propiedades, requisitos)

        if es_aceptable:
            razon = (
                f"Propuesta aceptable con {len(propiedades_propuesta)} propiedades "
                f"y score promedio de {score_promedio:.2f}."
            )
            diagnostico = "Evaluacion exitosa: la propuesta supera los umbrales definidos."
        elif not cantidad_suficiente:
            razon = (
                f"La propuesta tiene {len(propiedades_propuesta)} propiedades; "
                f"se requieren al menos {self.min_propiedades}."
            )
            diagnostico = "Fallo de evaluacion: cantidad insuficiente en la propuesta."
        else:
            razon = (
                f"El score de la propuesta ({score_promedio:.2f}) esta por debajo "
                f"del minimo aceptable ({self.score_minimo:.2f})."
            )
            diagnostico = "Fallo de evaluacion: score insuficiente."

        return self._resultado(
            es_aceptable=es_aceptable,
            score=score_promedio,
            razon=razon,
            recomendacion=recomendacion,
            diagnostico=diagnostico,
        )

    def _resultado(
        self,
        *,
        es_aceptable: bool,
        score: float,
        razon: str,
        recomendacion: str | None,
        diagnostico: str,
    ) -> dict[str, Any]:
        evaluacion = Evaluacion(
            es_aceptable=es_aceptable,
            score=round(score * 10, 2),
            razon=razon,
            recomendacion=recomendacion,
        )
        return {
            "evaluacion": evaluacion.model_dump(),
            "diagnostico": _combinar_diagnosticos(self._diagnostico_actual, diagnostico),
        }

    def _recomendar_relajacion(
        self,
        propiedades: list[Mapping[str, Any]],
        requisitos: Mapping[str, Any],
    ) -> str | None:
        if requisitos.get("precio_max") is not None:
            precio_max = float(requisitos["precio_max"])
            if all(float(prop.get("precio") or 0) > precio_max for prop in propiedades):
                return "precio_max"

        if requisitos.get("area_min") is not None:
            area_min = float(requisitos["area_min"])
            if all(float(prop.get("area") or 0) < area_min for prop in propiedades):
                return "area_min"

        if requisitos.get("habitaciones") is not None:
            habitaciones = int(requisitos["habitaciones"])
            if all(int(prop.get("habitaciones") or 0) < habitaciones for prop in propiedades):
                return "habitaciones"

        if requisitos.get("ubicacion"):
            return "ubicacion"
        if requisitos.get("tipo"):
            return "tipo"
        return "precio_max"


def evaluador(estado: Any) -> dict[str, Any]:
    """Nodo del grafo: evalua propuesta, propiedades y requisitos."""

    return EvaluadorResultados().evaluar(estado)


def evaluar_resultados(estado: Any) -> dict[str, Any]:
    """Alias de compatibilidad con el nombre anterior del nodo."""

    return evaluador(estado)


def _score_propiedad(propiedad: Mapping[str, Any], requisitos: Mapping[str, Any]) -> float:
    if propiedad.get("score") is not None:
        return float(propiedad["score"])

    puntos = 0.0
    total = 0

    comparaciones = [
        ("precio_max", "precio", lambda valor, limite: valor <= limite),
        ("area_min", "area", lambda valor, limite: valor >= limite),
        ("habitaciones", "habitaciones", lambda valor, limite: valor >= limite),
        ("banos", "banos", lambda valor, limite: valor >= limite),
        ("parqueadero", "parqueadero", lambda valor, limite: valor >= limite),
        ("administracion_max", "administracion", lambda valor, limite: valor is None or valor <= limite),
    ]

    for req_campo, prop_campo, cumple in comparaciones:
        if requisitos.get(req_campo) is None:
            continue
        total += 1
        if cumple(propiedad.get(prop_campo), requisitos[req_campo]):
            puntos += 1

    for campo in ("tipo", "ubicacion"):
        if requisitos.get(campo) is None:
            continue
        total += 1
        if str(requisitos[campo]).lower() in str(propiedad.get(campo, "")).lower():
            puntos += 1

    return puntos / total if total else 0.5


def _promedio(valores: list[float]) -> float:
    return sum(valores) / len(valores) if valores else 0.0


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
