from __future__ import annotations

import re
import unicodedata
from typing import Any


def extraer_requisitos_desde_texto(texto_usuario: str) -> dict[str, Any]:
    """Extrae requisitos explicitos con la forma del modelo Requisito."""

    texto = _normalizar_texto(texto_usuario)
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

    habitaciones = re.search(r"(\d+)\s*(habitaciones|habitacion|hab|cuartos?)", texto)
    if habitaciones:
        requisitos["habitaciones"] = int(habitaciones.group(1))

    banos = re.search(r"(\d+)\s*(banos|bano|baths?|bathrooms?)", texto)
    if banos:
        requisitos["banos"] = int(banos.group(1))

    area = re.search(
        r"(minimo|desde|al menos|mayor a|mas de)?\s*(\d+(?:[.,]\d+)?)\s*"
        r"(m2|mts2|metros cuadrados|metro cuadrado|metros|m cuadrad[oa]s?)",
        texto,
    )
    if area:
        requisitos["area_min"] = float(area.group(2).replace(",", "."))

    ubicacion = _extraer_ubicacion(texto_usuario)
    if ubicacion:
        requisitos["ubicacion"] = ubicacion

    if "parqueadero" in texto or "garaje" in texto:
        requisitos["parqueadero"] = 1

    return normalizar_requisitos_entrada(requisitos)


def normalizar_requisitos_entrada(requisitos: dict[str, Any]) -> dict[str, Any]:
    """Adapta alias comunes al modelo Requisito usado por el grafo."""

    normalizados = dict(requisitos or {})

    aliases = {
        "habitaciones_min": "habitaciones",
        "cuartos": "habitaciones",
        "banos_min": "banos",
        "area": "area_min",
        "area_minima": "area_min",
        "metros": "area_min",
        "precio": "precio_max",
        "presupuesto": "precio_max",
        "administracion": "administracion_max",
    }
    for origen, destino in aliases.items():
        if origen in normalizados and destino not in normalizados:
            normalizados[destino] = normalizados.pop(origen)

    for clave in list(normalizados):
        clave_normalizada = _normalizar_texto(clave)
        if clave_normalizada in {"banos", "banos_min"} and "banos" not in normalizados:
            normalizados["banos"] = normalizados.pop(clave)
        elif clave_normalizada in {"area minima", "area_minima"} and "area_min" not in normalizados:
            normalizados["area_min"] = normalizados.pop(clave)

    zonas = normalizados.pop("zonas_preferidas", None)
    if zonas and not normalizados.get("ubicacion"):
        if isinstance(zonas, list):
            normalizados["ubicacion"] = zonas[0] if zonas else None
        else:
            normalizados["ubicacion"] = zonas

    if normalizados.get("parqueadero") is True:
        normalizados["parqueadero"] = 1
    elif normalizados.get("parqueadero") is False:
        normalizados["parqueadero"] = 0

    tipo = normalizados.get("tipo")
    if isinstance(tipo, str):
        tipo_normalizado = _normalizar_texto(tipo).strip()
        if tipo_normalizado in {"apartamentos", "apto", "apto."}:
            tipo_normalizado = "apartamento"
        elif tipo_normalizado in {"casas"}:
            tipo_normalizado = "casa"
        normalizados["tipo"] = tipo_normalizado

    return {clave: valor for clave, valor in normalizados.items() if valor is not None}


def _extraer_precio_max(texto: str) -> float | None:
    match = re.search(r"(maximo|max|hasta)\s*(\d+(?:[.,]\d+)?)\s*(millones|m)", texto)
    if match:
        valor = float(match.group(2).replace(",", "."))
        return valor * 1_000_000

    match = re.search(r"(maximo|max|hasta)\s*\$?\s*(\d{5,12})\s*(pesos|cop)?", texto)
    if match:
        return float(match.group(2))

    match = re.search(r"\$\s*(\d{5,12})", texto)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d{5,12})\s*(pesos|cop)", texto)
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
    texto = _normalizar_texto(texto_usuario)
    for ubicacion in ubicaciones_conocidas:
        if _normalizar_texto(ubicacion) in texto:
            return ubicacion
    return None


def _normalizar_texto(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor).lower())
    return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
