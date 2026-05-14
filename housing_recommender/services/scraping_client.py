from __future__ import annotations

from typing import Any, Mapping, Protocol


class ScrapingClient(Protocol):
    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        ...


class MockScrapingClient:
    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [
            propiedad
            for propiedad in _propiedades_demo()
            if _cumple_requisitos(propiedad, requisitos)
        ]


def obtener_propiedades(
    requisitos: Mapping[str, Any],
    client: ScrapingClient | None = None,
) -> list[dict[str, Any]]:
    proveedor = client or MockScrapingClient()
    return proveedor.buscar(requisitos)


def _cumple_requisitos(propiedad: Mapping[str, Any], requisitos: Mapping[str, Any]) -> bool:
    if requisitos.get("ubicacion") and str(requisitos["ubicacion"]).lower() not in str(propiedad["ubicacion"]).lower():
        return False
    if requisitos.get("precio_max") is not None and propiedad["precio"] > requisitos["precio_max"]:
        return False
    if requisitos.get("habitaciones") is not None and propiedad["habitaciones"] < requisitos["habitaciones"]:
        return False
    if requisitos.get("baños") is not None and propiedad["baños"] < requisitos["baños"]:
        return False
    if requisitos.get("parqueadero") is not None and propiedad["parqueadero"] != requisitos["parqueadero"]:
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


def _propiedades_demo() -> list[dict[str, Any]]:
    return [
        {
            "ubicacion": "Norte",
            "precio": 800000000,
            "habitaciones": 3,
            "banos": 2,
            "parqueadero": True,
            "tipo": "apartamento",
            "area": 90,
            "administracion": 120000,
        },
        {
            "ubicacion": "Sur",
            "precio": 950000000,
            "habitaciones": 4,
            "banos": 3,
            "parqueadero": True,
            "tipo": "casa",
            "area": 110,
            "administracion": None,
        },
        {
            "ubicacion": "Centro",
            "precio": 700000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": False,
            "tipo": "apartamento",
            "area": 75,
            "administracion": 90000,
        },
        {
            "ubicacion": "Norte",
            "precio": 1100000000,
            "habitaciones": 4,
            "banos": 3,
            "parqueadero": True,
            "tipo": "casa",
            "area": 130,
            "administracion": None,
        },
        {
            "ubicacion": "Sur",
            "precio": 600000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": False,
            "tipo": "apartamento",
            "area": 60,
            "administracion": 80000,
        },
    ]
