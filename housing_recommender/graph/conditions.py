"""
Funciones de condición para las transiciones del grafo.
Determinan qué camino seguir basándose en el estado actual.
"""

from typing import Dict, Any, Literal


def decidir_siguiente_paso(
    state: Dict[str, Any]
) -> Literal["presentar", "relajar", "finalizar"]:
    """
    Decide el siguiente paso después de evaluar resultados.
    
    Args:
        state: Estado actual del sistema
        
    Returns:
        "presentar": Si los resultados son aceptables
        "relajar": Si se necesitan relajar criterios
        "finalizar": Si se alcanzó el límite de iteraciones
    """
    evaluacion = state.get('evaluacion', {})
    es_aceptable = evaluacion.get('es_aceptable', False)
    iteracion = state.get('iteracion_relajacion', 0)
    max_iteraciones = 5
    
    # Si los resultados son aceptables, presentar
    if es_aceptable:
        return "presentar"
    
    # Si se alcanzó el límite de iteraciones, finalizar
    if iteracion >= max_iteraciones:
        return "finalizar"
    
    # Caso contrario, relajar criterios
    return "relajar"


def debe_continuar(
    state: Dict[str, Any]
) -> Literal["continuar", "finalizar"]:
    """
    Decide si continuar después de relajar criterios.
    
    Args:
        state: Estado actual del sistema
        
    Returns:
        "continuar": Si se puede seguir buscando
        "finalizar": Si se alcanzó el límite
    """
    relajacion_completa = state.get('relajacion_completa', False)
    iteracion = state.get('iteracion_relajacion', 0)
    max_iteraciones = 5
    
    if relajacion_completa or iteracion >= max_iteraciones:
        return "finalizar"
    
    return "continuar"


def requiere_relajacion(state: Dict[str, Any]) -> bool:
    """
    Determina si se requiere relajación de criterios.
    
    Args:
        state: Estado actual del sistema
        
    Returns:
        True si se necesita relajar, False si no
    """
    evaluacion = state.get('evaluacion', {})
    return not evaluacion.get('es_aceptable', False)


def tiene_resultados_minimos(state: Dict[str, Any]) -> bool:
    """
    Verifica si hay resultados mínimos aceptables.
    
    Args:
        state: Estado actual del sistema
        
    Returns:
        True si hay suficientes resultados
    """
    propiedades = state.get('propiedades_filtradas', [])
    min_requerido = 2
    return len(propiedades) >= min_requerido


def puede_relajar_mas(state: Dict[str, Any]) -> bool:
    """
    Verifica si aún es posible relajar más criterios.
    
    Args:
        state: Estado actual del sistema
        
    Returns:
        True si se puede seguir relajando
    """
    iteracion = state.get('iteracion_relajacion', 0)
    max_iteraciones = 5
    relajacion_completa = state.get('relajacion_completa', False)
    
    return iteracion < max_iteraciones and not relajacion_completa