"""
Constructor del grafo de estados del sistema de recomendación.
Define la estructura del flujo de decisión usando LangGraph.
"""

from typing import Dict, Any, Literal, TypedDict
from langgraph.graph import StateGraph, END

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
    # Importar funciones de nodos (que se implementar en otros módulos)
    from nodes.evaluador import evaluar_resultados
    from nodes.agente_relajacion import relajar_condiciones
    from conditions import decidir_siguiente_paso, debe_continuar
    
    # Crear el grafo
    workflow = StateGraph(EstadoSistema)
    
    # Nodos del grafo (estos deben implementarse)
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
            "finalizar": END
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


# Funciones de nodos placeholder (que están en módulos separados)

def interpretar_requisitos(state: EstadoSistema) -> EstadoSistema:
    """Interpreta y estructura los requerimientos del usuario."""
    # Implementación básica
    return {
        **state,
        'criterios_actuales': state.get('criterios_originales', {}),
        'iteracion_relajacion': 0,
        'historial_relajacion': [],
        'relajacion_completa': False
    }


def identificar_zonas(state: EstadoSistema) -> EstadoSistema:
    """Identifica zonas relevantes según criterios."""
    # Implementación placeholder
    zonas = ["El Poblado", "Laureles", "Envigado", "Sabaneta"]
    return {
        **state,
        'zonas_analizadas': zonas
    }


def evaluar_zonas(state: EstadoSistema) -> EstadoSistema:
    """Evalúa las zonas identificadas."""
    # Implementación placeholder
    return {
        **state,
        'zonas_seleccionadas': state.get('zonas_analizadas', [])[:3]
    }


def buscar_propiedades(state: EstadoSistema) -> EstadoSistema:
    """Busca propiedades en las zonas seleccionadas."""
    # Implementación placeholder (Acá va la integración con la API inmobiliaria)
    propiedades_mock = [
        {
            'id': 1,
            'precio': state['criterios_actuales'].get('precio_max', 300000000) * 0.9,
            'area': state['criterios_actuales'].get('area_min', 70) * 1.1,
            'habitaciones': state['criterios_actuales'].get('habitaciones_min', 2),
            'zona': state.get('zonas_seleccionadas', ['El Poblado'])[0],
            'tipo': 'apartamento'
        }
    ]
    
    return {
        **state,
        'propiedades_encontradas': propiedades_mock
    }


def filtrar_propiedades(state: EstadoSistema) -> EstadoSistema:
    """Filtra propiedades según criterios actuales."""
    propiedades = state.get('propiedades_encontradas', [])
    criterios = state.get('criterios_actuales', {})
    
    filtradas = [
        p for p in propiedades
        if p.get('precio', 0) <= criterios.get('precio_max', float('inf'))
    ]
    
    return {
        **state,
        'propiedades_filtradas': filtradas
    }


def presentar_resultados_nodo(state: EstadoSistema) -> EstadoSistema:
    """Prepara resultados finales para presentación."""
    from nodes.presentar_resultado import generar_recomendaciones
    
    recomendaciones, explicaciones = generar_recomendaciones(state)
    
    return {
        **state,
        'recomendaciones_finales': recomendaciones,
        'explicaciones': explicaciones
    }