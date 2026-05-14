# nodes/interpretar_requisitos.py
"""
Nodo 1 del grafo: interpreta el texto libre del usuario y lo transforma 
en un objeto Requisito estructurado.

Este nodo también se ejecuta en iteraciones posteriores cuando el ciclo 
de relajación lo invoca para refinar los requisitos.
"""

from pathlib import Path
from services.llm_client import get_llm
from langchain_core.prompts import ChatPromptTemplate

from state.models import AgentState, Requisito
from config.settings import settings


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
    # 1. Preparar el LLM con structured output sobre nuestro modelo Pydantic
    llm = get_llm(temperature=0)
    llm_estructurado = llm.with_structured_output(Requisito)

    # 2. Construir el prompt rellenando los placeholders
    requisitos_previos_str = (
        state.requisitos.model_dump_json(indent=2)
        if state.requisitos is not None
        else "Ninguno. Esta es la primera iteración."
    )

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    mensaje = prompt.format(
        texto_usuario=state.textoUsuario,
        requisitos_previos=requisitos_previos_str,
    )

    # 3. Invocar al LLM
    requisitos_extraidos: Requisito = llm_estructurado.invoke(mensaje)

    # 4. Devolver la actualización del estado
    return {"requisitos": requisitos_extraidos}