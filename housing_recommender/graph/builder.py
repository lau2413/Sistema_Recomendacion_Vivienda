"""
Constructor del grafo de estados del sistema de recomendación.
Define la estructura del flujo de decisión usando LangGraph.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from housing_recommender.state.models import AgentState
from housing_recommender.graph.conditions import decidir_siguiente_paso, debe_continuar


# ============================================================
# STUBS DE NODOS (retornan {} hasta que cada persona conecte su implementación real)
# ============================================================

def interpretar_requisitos(state: AgentState) -> dict:
    return {}


def identificar_zonas(state: AgentState) -> dict:
    return {}


def evaluar_zonas(state: AgentState) -> dict:
    return {}


def buscar_propiedades(state: AgentState) -> dict:
    return {}


def filtrar_propiedades(state: AgentState) -> dict:
    return {}


def evaluar_resultados(state: AgentState) -> dict:
    return {}


def relajar_condiciones(state: AgentState) -> dict:
    # El stub incrementa iteracion para que el loop termine al llegar a max_iteraciones.
    # La implementación real de Persona 1 reemplazará esto.
    return {"iteracion": state.iteracion + 1}


def presentar_resultados(state: AgentState) -> dict:
    return {}


# ============================================================
# CONSTRUCCIÓN DEL GRAFO
# ============================================================

def construir_grafo():
    """
    Construye el grafo de estados del sistema de recomendación.

    Returns:
        Grafo compilado listo para ejecución.
    """
    workflow = StateGraph(AgentState)

    # Nodos
    workflow.add_node("interpretar_requisitos", interpretar_requisitos)
    workflow.add_node("identificar_zonas", identificar_zonas)
    workflow.add_node("evaluar_zonas", evaluar_zonas)
    workflow.add_node("buscar_propiedades", buscar_propiedades)
    workflow.add_node("filtrar_propiedades", filtrar_propiedades)
    workflow.add_node("evaluar_resultados", evaluar_resultados)
    workflow.add_node("relajar_condiciones", relajar_condiciones)
    workflow.add_node("presentar_resultados", presentar_resultados)

    # Punto de entrada
    workflow.set_entry_point("interpretar_requisitos")

    # Flujo principal
    workflow.add_edge("interpretar_requisitos", "identificar_zonas")
    workflow.add_edge("identificar_zonas", "evaluar_zonas")
    workflow.add_edge("evaluar_zonas", "buscar_propiedades")
    workflow.add_edge("buscar_propiedades", "filtrar_propiedades")
    workflow.add_edge("filtrar_propiedades", "evaluar_resultados")

    # Decisión condicional después de evaluación
    workflow.add_conditional_edges(
        "evaluar_resultados",
        decidir_siguiente_paso,
        {
            "presentar": "presentar_resultados",
            "relajar": "relajar_condiciones",
            "finalizar": END,
        },
    )

    # Después de relajar, volver a buscar o finalizar
    workflow.add_conditional_edges(
        "relajar_condiciones",
        debe_continuar,
        {
            "continuar": "buscar_propiedades",
            "finalizar": "presentar_resultados",
        },
    )

    workflow.add_edge("presentar_resultados", END)

    return workflow.compile()
