# nodes/interpretar_requisitos.py
"""
Nodo 1 del grafo: interpreta el texto libre del usuario y lo transforma 
en un objeto Requisito estructurado.

Este nodo también se ejecuta en iteraciones posteriores cuando el ciclo 
de relajación lo invoca para refinar los requisitos.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_recommender.services.llm_client import generar_json_estructurado
from housing_recommender.services.requisitos_parser import extraer_requisitos_desde_texto
from housing_recommender.state.models import AgentState, Requisito


# Carga el prompt desde el archivo de texto (una sola vez, al importar el módulo)
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "ajustar_requisitos.txt"
PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


def interpretar_requisitos(state: AgentState) -> dict:
    """
    Toma state.textoUsuario y devuelve un dict con el campo 'requisitos' 
    poblado con un objeto Requisito.

    Args:
        state: estado actual del grafo.

    Returns:
        dict con la clave 'requisitos' que LangGraph fusionará en el estado.
    """
    requisitos_previos_str = (
        state.requisitos.model_dump_json(indent=2)
        if state.requisitos is not None
        else "Ninguno. Esta es la primera iteración."
    )

    mensaje = PROMPT_TEMPLATE.format(
        texto_usuario=state.textoUsuario,
        requisitos_previos=requisitos_previos_str,
    )

    requisitos_extraidos = generar_json_estructurado(mensaje)
    if requisitos_extraidos is None:
        requisitos_extraidos = extraer_requisitos_desde_texto(state.textoUsuario)

    return {"requisitos": Requisito(**requisitos_extraidos)}
