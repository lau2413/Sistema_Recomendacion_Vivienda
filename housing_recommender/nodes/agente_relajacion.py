"""Nodo de relajacion progresiva de requisitos."""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_recommender.state.models import EntradaRelajacion


class AgenteRelajacion:
    """Modifica requisitos actuales y registra cada cambio realizado."""

    def __init__(self, factor_precio: float = 0.10, factor_area: float = 0.10) -> None:
        self.factor_precio = factor_precio
        self.factor_area = factor_area

    def relajar_requisitos(self, estado: Any) -> dict[str, Any]:
        iteracion_actual = int(_get(estado, "iteracion", 0) or 0)
        max_iteraciones = int(_get(estado, "max_iteraciones", 3) or 3)

        if iteracion_actual >= max_iteraciones:
            return {
                "relajacion_completa": True,
                "mensaje_relajacion": "Se alcanzo el limite maximo de relajaciones.",
                "diagnostico": _combinar_diagnosticos(
                    _get(estado, "diagnostico"),
                    "Fallo de relajacion: limite de iteraciones alcanzado.",
                ),
            }

        requisitos = deepcopy(_a_dict(_get(estado, "requisitos", {}) or {}))
        historial = list(_get(estado, "historial_relajacion", []) or [])
        evaluacion = _a_dict(_get(estado, "evaluacion", {}) or {})
        campo_recomendado = evaluacion.get("recomendacion")

        cambio = self._aplicar_relajacion(requisitos, campo_recomendado, iteracion_actual)
        nueva_iteracion = iteracion_actual + 1

        if cambio is None:
            return {
                "iteracion": nueva_iteracion,
                "relajacion_completa": True,
                "mensaje_relajacion": "No hay requisitos relajables disponibles.",
                "diagnostico": _combinar_diagnosticos(
                    _get(estado, "diagnostico"),
                    "Fallo de relajacion: no se encontro un campo modificable.",
                ),
            }

        entrada = EntradaRelajacion(iteracion=nueva_iteracion, **cambio).model_dump()
        historial.append(entrada)
        mensaje = f"Requisito relajado: {entrada['descripcion']}"

        return {
            "requisitos": requisitos,
            "historial_relajacion": historial,
            "iteracion": nueva_iteracion,
            "mensaje_relajacion": mensaje,
            "relajacion_completa": nueva_iteracion >= max_iteraciones,
            "diagnostico": _combinar_diagnosticos(_get(estado, "diagnostico"), mensaje),
        }

    def _aplicar_relajacion(
        self,
        requisitos: dict[str, Any],
        campo_recomendado: str | None,
        iteracion: int,
    ) -> dict[str, Any] | None:
        candidatos = [
            campo_recomendado,
            ("precio_max", "area_min", "habitaciones")[iteracion % 3],
            "precio_max",
            "area_min",
            "habitaciones",
            "ubicacion",
            "tipo",
        ]

        for campo in candidatos:
            if campo == "precio_max" and requisitos.get("precio_max") is not None:
                anterior = requisitos["precio_max"]
                nuevo = round(float(anterior) * (1 + self.factor_precio), 2)
                requisitos["precio_max"] = nuevo
                return _cambio(campo, anterior, nuevo, "precio_max aumento 10%")

            if campo == "area_min" and requisitos.get("area_min") is not None:
                anterior = requisitos["area_min"]
                nuevo = max(1, round(float(anterior) * (1 - self.factor_area), 2))
                requisitos["area_min"] = nuevo
                return _cambio(campo, anterior, nuevo, "area_min se redujo 10%")

            if campo == "habitaciones" and requisitos.get("habitaciones") is not None:
                anterior = int(requisitos["habitaciones"])
                if anterior <= 1:
                    continue
                nuevo = anterior - 1
                requisitos["habitaciones"] = nuevo
                return _cambio(campo, anterior, nuevo, "habitaciones minimas bajaron en 1")

            if campo == "ubicacion" and requisitos.get("ubicacion"):
                anterior = requisitos["ubicacion"]
                requisitos.pop("ubicacion", None)
                return _cambio(campo, anterior, None, "se amplio la busqueda a mas zonas")

            if campo == "tipo" and requisitos.get("tipo"):
                anterior = requisitos["tipo"]
                requisitos.pop("tipo", None)
                return _cambio(campo, anterior, None, "se permitieron otros tipos de vivienda")

        return None


def agente_relajacion(estado: Any) -> dict[str, Any]:
    """Nodo del grafo: modifica requisitos y registra historial_relajacion."""

    return AgenteRelajacion().relajar_requisitos(estado)


def relajar_condiciones(estado: Any) -> dict[str, Any]:
    """Alias de compatibilidad con el nombre anterior del nodo."""

    return agente_relajacion(estado)


def _cambio(campo: str, antes: Any, despues: Any, descripcion: str) -> dict[str, Any]:
    return {
        "campo_relajado": campo,
        "valor_antes": antes,
        "valor_despues": despues,
        "descripcion": descripcion,
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
