"""
Funciones de condición para las transiciones del grafo.
Determinan qué camino seguir basándose en el estado actual.
"""

from typing import Any, Literal, Union


def _get(state: Any, field: str, default: Any = None) -> Any:
    """Lee un campo del estado, sea Pydantic BaseModel o dict."""
    if isinstance(state, dict):
        return state.get(field, default)
    return getattr(state, field, default)


def decidir_siguiente_paso(state: Any) -> Literal["presentar", "relajar", "finalizar"]:
    """
    Decide el siguiente paso después de evaluar resultados.

    Returns:
        "presentar": Si los resultados son aceptables.
        "relajar": Si se necesita relajar criterios.
        "finalizar": Si se alcanzó el límite de iteraciones.
    """
    evaluacion = _get(state, 'evaluacion')
    if evaluacion is None:
        es_aceptable = False
    elif isinstance(evaluacion, dict):
        es_aceptable = evaluacion.get('es_aceptable', False)
    else:
        es_aceptable = getattr(evaluacion, 'es_aceptable', False)

    iteracion = _get(state, 'iteracion', 0)
    max_iteraciones = _get(state, 'max_iteraciones', 3)

    if es_aceptable:
        return "presentar"
    if iteracion >= max_iteraciones:
        return "finalizar"
    return "relajar"


def debe_continuar(state: Any) -> Literal["continuar", "finalizar"]:
    """
    Decide si continuar buscando después de relajar criterios.

    Returns:
        "continuar": Si se puede seguir buscando.
        "finalizar": Si se alcanzó el límite o la relajación está completa.
    """
    relajacion_completa = _get(state, 'relajacion_completa', False)
    iteracion = _get(state, 'iteracion', 0)
    max_iteraciones = _get(state, 'max_iteraciones', 3)

    if relajacion_completa or iteracion >= max_iteraciones:
        return "finalizar"
    return "continuar"


def requiere_relajacion(state: Any) -> bool:
    """Determina si se requiere relajación de criterios."""
    evaluacion = _get(state, 'evaluacion')
    if evaluacion is None:
        return True
    if isinstance(evaluacion, dict):
        return not evaluacion.get('es_aceptable', False)
    return not getattr(evaluacion, 'es_aceptable', False)


def tiene_resultados_minimos(state: Any) -> bool:
    """Verifica si hay al menos 2 propiedades filtradas."""
    propiedades = _get(state, 'propiedades_filtradas') or []
    return len(propiedades) >= 2


def puede_relajar_mas(state: Any) -> bool:
    """Verifica si aún es posible relajar más criterios."""
    iteracion = _get(state, 'iteracion', 0)
    max_iteraciones = _get(state, 'max_iteraciones', 3)
    relajacion_completa = _get(state, 'relajacion_completa', False)
    return iteracion < max_iteraciones and not relajacion_completa
