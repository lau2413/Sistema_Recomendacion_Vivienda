"""Constructor del grafo de estados del sistema de recomendacion."""

from __future__ import annotations

import sys
from pathlib import Path

from langgraph.graph import END, StateGraph

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_recommender.graph.conditions import decidir_siguiente_paso, debe_continuar
from housing_recommender.graph.nodes import (
    agente_noticias,
    agente_relajacion,
    ajustar_requisitos,
    construir_propuesta,
    evaluador,
    presentar_resultado,
    propiedades_scraping,
    zonas_contexto,
)
from housing_recommender.state.models import AgentState


def construir_grafo():
    """Construye el grafo compilado con el estado AgentState."""

    workflow = StateGraph(AgentState)

    workflow.add_node("ajustar_requisitos", ajustar_requisitos)
    workflow.add_node("zonas_contexto", zonas_contexto)
    workflow.add_node("propiedades_scraping", propiedades_scraping)
    workflow.add_node("agente_noticias", agente_noticias)
    workflow.add_node("construir_propuesta", construir_propuesta)
    workflow.add_node("evaluador", evaluador)
    workflow.add_node("agente_relajacion", agente_relajacion)
    workflow.add_node("presentar_resultado", presentar_resultado)

    workflow.set_entry_point("ajustar_requisitos")

    workflow.add_edge("ajustar_requisitos", "zonas_contexto")
    workflow.add_edge("zonas_contexto", "propiedades_scraping")
    workflow.add_edge("propiedades_scraping", "agente_noticias")
    workflow.add_edge("agente_noticias", "construir_propuesta")
    workflow.add_edge("construir_propuesta", "evaluador")

    workflow.add_conditional_edges(
        "evaluador",
        decidir_siguiente_paso,
        {
            "presentar": "presentar_resultado",
            "relajar": "agente_relajacion",
            "finalizar": "presentar_resultado",
        },
    )

    workflow.add_conditional_edges(
        "agente_relajacion",
        debe_continuar,
        {
            "continuar": "zonas_contexto",
            "finalizar": "presentar_resultado",
        },
    )

    workflow.add_edge("presentar_resultado", END)

    return workflow.compile()