from __future__ import annotations

import re
from typing import Any


def extraer_requisitos_desde_texto(texto_usuario: str) -> dict[str, Any]:
    """Extrae requisitos explicitos con la forma del modelo Requisito."""

    texto = texto_usuario.lower()
    requisitos: dict[str, Any] = {}

    if "apartamento" in texto:
        requisitos["tipo"] = "apartamento"
    elif "apartaestudio" in texto:
        requisitos["tipo"] = "apartaestudio"
    elif "casa" in texto:
        requisitos["tipo"] = "casa"

    precio_max = _extraer_precio_max(texto)
    if precio_max is not None:
        requisitos["precio_max"] = precio_max

    habitaciones = re.search(r"(\d+)\s*(habitaciones|habitacion|hab)", texto)
    if habitaciones:
        requisitos["habitaciones"] = int(habitaciones.group(1))

    banos = re.search(r"(\d+)\s*(banos|bano|baños|baño)", texto)
    if banos:
        requisitos["banos"] = int(banos.group(1))

    area = re.search(r"(minimo|desde|al menos)?\s*(\d+)\s*m2", texto)
    if area:
        requisitos["area_min"] = float(area.group(2))

    ubicacion = _extraer_ubicacion(texto_usuario)
    if ubicacion:
        requisitos["ubicacion"] = ubicacion

    if "parqueadero" in texto or "garaje" in texto:
        requisitos["parqueadero"] = True

    return requisitos


def _extraer_precio_max(texto: str) -> float | None:
    match = re.search(r"(maximo|max|hasta)\s*(\d+(?:[.,]\d+)?)\s*(millones|m)", texto)
    if match:
        valor = float(match.group(2).replace(",", "."))
        return valor * 1_000_000

    match = re.search(r"\$?\s*(\d{7,12})", texto)
    if match:
        return float(match.group(1))

    return None


def _extraer_ubicacion(texto_usuario: str) -> str | None:
    ubicaciones_conocidas = [
        "Laureles",
        "Belen",
        "Envigado",
        "Poblado",
        "Sabaneta",
        "Robledo",
        "Norte",
        "Sur",
        "Centro",
    ]
    texto = texto_usuario.lower()
    for ubicacion in ubicaciones_conocidas:
        if ubicacion.lower() in texto:
            return ubicacion
    return None
