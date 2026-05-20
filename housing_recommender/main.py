"""Punto de entrada principal del sistema de recomendacion de viviendas."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from housing_recommender.graph.builder import construir_grafo
from housing_recommender.nodes.presentar_resultado import presentar_resultados


def ejecutar_sistema(criterios_usuario: dict[str, Any] | str):
    """Ejecuta el grafo completo con texto libre o requisitos estructurados."""

    print("\n" + "=" * 80)
    print("--SISTEMA DE RECOMENDACION DE VIVIENDAS--")
    print("=" * 80 + "\n")

    app = construir_grafo()

    if isinstance(criterios_usuario, str):
        texto_usuario = criterios_usuario
        requisitos = None
    else:
        texto_usuario = ""
        requisitos = dict(criterios_usuario)

    estado_inicial = {
        "textoUsuario": texto_usuario,
        "requisitos_originales": dict(requisitos) if requisitos else None,
        "requisitos": requisitos,
        "zonas_analizadas": [],
        "zonas_seleccionadas": [],
        "propiedades": None,
        "noticias": None,
        "propuesta": None,
        "evaluacion": None,
        "historial_relajacion": [],
        "iteracion": 0,
        "max_iteraciones": 3,
        "relajacion_completa": False,
        "nivel_relajacion_aplicado": 0.0,
        "diagnostico": "",
        "mensaje_relajacion": "",
        "recomendaciones_finales": [],
        "explicaciones": [],
    }

    resultado = app.invoke(estado_inicial)
    presentar_resultados(resultado)
    return resultado


if __name__ == "__main__":
    criterios_ejemplo = {
        "precio_max": 300_000_000,
        "area_min": 70,
        "habitaciones": 2,
        "tipo": "apartamento",
        "ubicacion": "Laureles",
    }

    ejecutar_sistema(criterios_ejemplo)
