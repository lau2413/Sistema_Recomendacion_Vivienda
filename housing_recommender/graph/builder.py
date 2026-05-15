"""
Constructor del grafo de estados del sistema de recomendación.
Define la estructura del flujo de decisión usando LangGraph.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict


class EstadoSistema(TypedDict):
    """Definición del estado compartido del sistema."""
    # Criterios
    criterios_originales: Dict[str, Any]
    criterios_actuales: Dict[str, Any]
    
    # Información de zonas
    zonas_analizadas: list
    zonas_seleccionadas: list
    
    # Resultados de búsqueda
    propiedades_encontradas: list
    propiedades_filtradas: list
    
    # Evaluación
    evaluacion: Dict[str, Any]
    
    # Historial y control
    historial_relajacion: list
    iteracion_relajacion: int
    relajacion_completa: bool
    
    # Diagnóstico
    diagnostico: str
    mensaje_relajacion: str
    
    # Resultados finales
    recomendaciones_finales: list
    explicaciones: list


def construir_grafo():
    """
    Construye el grafo de estados del sistema de recomendación.
    
    Returns:
        Grafo compilado listo para ejecución
    """
    # Importar funciones de nodos
    from housing_recommender.nodes.evaluador import evaluar_resultados
    from housing_recommender.nodes.agente_relajacion import relajar_condiciones
    from housing_recommender.graph.conditions import decidir_siguiente_paso, debe_continuar
    from housing_recommender.graph.nodes import (
        interpretar_requisitos,
        identificar_zonas,
        evaluar_zonas,
        buscar_propiedades,
        filtrar_propiedades,
        presentar_resultados_nodo
    )
    
    # Crear el grafo
    workflow = StateGraph(EstadoSistema)
    
    # Agregar nodos
    workflow.add_node("interpretar_requisitos", interpretar_requisitos)
    workflow.add_node("identificar_zonas", identificar_zonas)
    workflow.add_node("evaluar_zonas", evaluar_zonas)
    workflow.add_node("buscar_propiedades", buscar_propiedades)
    workflow.add_node("filtrar_propiedades", filtrar_propiedades)
    workflow.add_node("evaluar_resultados", evaluar_resultados)
    workflow.add_node("relajar_condiciones", relajar_condiciones)
    workflow.add_node("presentar_resultados", presentar_resultados_nodo)
    
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
            "finalizar": "presentar_resultados"
        }
    )
    
    # Después de relajar, volver a buscar
    workflow.add_conditional_edges(
        "relajar_condiciones",
        debe_continuar,
        {
            "continuar": "buscar_propiedades",
            "finalizar": "presentar_resultados"
        }
    )
    
    # Presentar resultados va al final
    workflow.add_edge("presentar_resultados", END)
    
    # Compilar el grafo
    app = workflow.compile()
    
    return app