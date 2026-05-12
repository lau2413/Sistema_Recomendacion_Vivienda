from __future__ import annotations

import re
from typing import Any


def extraer_criterios_desde_texto(mensaje: str) -> dict[str, Any]:
    """Extract explicit housing criteria using CriteriosUsuario field names."""

    texto = mensaje.lower()
    criterios: dict[str, Any] = {}

    if "apartamento" in texto:
        criterios["tipo_inmueble"] = "apartamento"
    elif "casa" in texto:
        criterios["tipo_inmueble"] = "casa"

    presupuesto = _extraer_presupuesto(texto)
    if presupuesto is not None:
        criterios["precio_max"] = presupuesto

    habitaciones = re.search(r"(\d+)\s*(habitaciones|habitacion|hab)", texto)
    if habitaciones:
        criterios["habitaciones_min"] = int(habitaciones.group(1))

    area = re.search(r"(minimo|desde|al menos)?\s*(\d+)\s*m2", texto)
    if area:
        criterios["area_min"] = int(area.group(2))

    zonas = _extraer_zonas(mensaje)
    if zonas:
        criterios["barrios_preferidos"] = zonas

    return criterios


def _extraer_presupuesto(texto: str) -> int | None:
    match = re.search(r"(maximo|max|hasta)\s*(\d+(?:[.,]\d+)?)\s*(millones|m)", texto)
    if match:
        valor = float(match.group(2).replace(",", "."))
        return int(valor * 1_000_000)

    match = re.search(r"\$?\s*(\d{7,12})", texto)
    if match:
        return int(match.group(1))

    return None


def _extraer_zonas(mensaje: str) -> list[str]:
    zonas_conocidas = {
        "laureles": "Laureles",
        "belen": "Belen",
        "belén": "Belen",
        "envigado": "Envigado",
        "poblado": "Poblado",
        "el poblado": "Poblado",
        "sabaneta": "Sabaneta",
        "robledo": "Robledo",
    }
    texto = mensaje.lower()
    zonas: list[str] = []
    for patron, nombre in zonas_conocidas.items():
        if patron in texto and nombre not in zonas:
            zonas.append(nombre)
    return zonas
