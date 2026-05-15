from __future__ import annotations

from typing import Any, Mapping, Protocol


class ScrapingClient(Protocol):
    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        ...


class MockScrapingClient:
    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        requisitos_normalizados = _normalizar_requisitos(requisitos)
        return [
            propiedad
            for propiedad in _propiedades_demo()
            if _cumple_requisitos(propiedad, requisitos_normalizados)
        ]


def obtener_propiedades(
    requisitos: Mapping[str, Any],
    client: ScrapingClient | None = None,
) -> list[dict[str, Any]]:
    proveedor = client or MockScrapingClient()
    return [_normalizar_propiedad(propiedad) for propiedad in proveedor.buscar(requisitos)]


def _cumple_requisitos(propiedad: Mapping[str, Any], requisitos: Mapping[str, Any]) -> bool:
    if requisitos.get("ubicacion") and not _ubicacion_coincide(propiedad["ubicacion"], requisitos["ubicacion"]):
        return False
    if requisitos.get("precio_max") is not None and propiedad["precio"] > requisitos["precio_max"]:
        return False
    if requisitos.get("habitaciones") is not None and propiedad["habitaciones"] < requisitos["habitaciones"]:
        return False
    if requisitos.get("banos") is not None and propiedad["banos"] < requisitos["banos"]:
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


def _normalizar_requisitos(requisitos: Mapping[str, Any]) -> dict[str, Any]:
    normalizados = dict(requisitos)

    if "baños" in normalizados and "banos" not in normalizados:
        normalizados["banos"] = normalizados.pop("baños")
    if "baÃ±os" in normalizados and "banos" not in normalizados:
        normalizados["banos"] = normalizados.pop("baÃ±os")

    if normalizados.get("parqueadero") is not None:
        normalizados["parqueadero"] = int(bool(normalizados["parqueadero"]))

    return {clave: valor for clave, valor in normalizados.items() if valor is not None}


def _normalizar_propiedad(propiedad: Mapping[str, Any]) -> dict[str, Any]:
    normalizada = dict(propiedad)
    normalizada["parqueadero"] = int(bool(normalizada.get("parqueadero", 0)))
    return normalizada


def _propiedades_demo() -> list[dict[str, Any]]:
    return [
        {
            "ubicacion": "El Poblado",
            "precio": 760000000,
            "habitaciones": 3,
            "banos": 2,
            "parqueadero": 1,
            "tipo": "apartamento",
            "area": 92,
            "administracion": 420000,
        },
        {
            "ubicacion": "Laureles",
            "precio": 590000000,
            "habitaciones": 3,
            "banos": 2,
            "parqueadero": 1,
            "tipo": "apartamento",
            "area": 84,
            "administracion": 310000,
        },
        {
            "ubicacion": "Envigado",
            "precio": 680000000,
            "habitaciones": 4,
            "banos": 3,
            "parqueadero": 1,
            "tipo": "casa",
            "area": 118,
            "administracion": None,
        },
        {
            "ubicacion": "Belen",
            "precio": 410000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": 0,
            "tipo": "apartamento",
            "area": 68,
            "administracion": 180000,
        },
        {
            "ubicacion": "Sabaneta",
            "precio": 360000000,
            "habitaciones": 2,
            "banos": 2,
            "parqueadero": 1,
            "tipo": "apartamento",
            "area": 63,
            "administracion": 220000,
        },
        {
            "ubicacion": "Centro",
            "precio": 285000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": 0,
            "tipo": "apartamento",
            "area": 58,
            "administracion": 120000,
        },
        {
            "ubicacion": "El Poblado",
            "precio": 980000000,
            "habitaciones": 4,
            "banos": 3,
            "parqueadero": 1,
            "tipo": "casa",
            "area": 135,
            "administracion": None,
        },
        {
            "ubicacion": "Robledo",
            "precio": 320000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": 0,
            "tipo": "apartamento",
            "area": 64,
            "administracion": 95000,
        },
    ]
