"""
Módulo de evaluación de resultados.
Evalúa si las propiedades encontradas cumplen con los criterios
y determina si se necesitan relajar las condiciones.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class EvaluacionResultado:
    """Resultado de la evaluación de propiedades."""
    es_aceptable: bool
    score: float
    razon: str
    recomendaciones: List[str]
    metricas: Dict[str, float]


class EvaluadorResultados:
    """
    Evalúa la calidad de los resultados de búsqueda.
    Determina si se debe continuar con relajación o presentar resultados.
    """
    
    def __init__(self, min_propiedades: int = 3, score_minimo: float = 0.6):
        self.min_propiedades = min_propiedades
        self.score_minimo = score_minimo
    
    def evaluar(self, state: Dict[str, Any]) -> EvaluacionResultado:
        """
        Evalúa los resultados actuales del estado.
        
        Args:
            state: Estado actual del sistema con propiedades encontradas
            
        Returns:
            EvaluacionResultado con la decisión de aceptación
        """
        propiedades = state.get('propiedades_filtradas', [])
        criterios_actuales = state.get('criterios_actuales', {})
        criterios_originales = state.get('criterios_originales', {})
        
        # Verificar cantidad mínima
        cantidad_suficiente = len(propiedades) >= self.min_propiedades
        
        if not propiedades:
            return EvaluacionResultado(
                es_aceptable=False,
                score=0.0,
                razon="No se encontraron propiedades que cumplan los criterios",
                recomendaciones=["Relajar restricciones de precio o área"],
                metricas={'cantidad': 0, 'cumplimiento_promedio': 0.0}
            )
        
        # Calcular score de cumplimiento para cada propiedad
        scores_propiedades = []
        for prop in propiedades:
            score_prop = self._calcular_score_propiedad(prop, criterios_actuales)
            scores_propiedades.append(score_prop)
        
        score_promedio = sum(scores_propiedades) / len(scores_propiedades)
        
        # Calcular nivel de relajación aplicado
        nivel_relajacion = self._calcular_nivel_relajacion(
            criterios_originales, 
            criterios_actuales
        )
        
        # Decisión de aceptabilidad
        es_aceptable = (
            cantidad_suficiente and 
            score_promedio >= self.score_minimo
        )
        
        # Generar razón y recomendaciones
        if es_aceptable:
            razon = (
                f"Se encontraron {len(propiedades)} propiedades con un "
                f"score promedio de {score_promedio:.2f}. "
                f"Nivel de relajación: {nivel_relajacion:.1%}"
            )
            recomendaciones = []
        else:
            razon = self._generar_razon_rechazo(
                len(propiedades), 
                score_promedio, 
                cantidad_suficiente
            )
            recomendaciones = self._generar_recomendaciones(
                propiedades, 
                criterios_actuales
            )
        
        return EvaluacionResultado(
            es_aceptable=es_aceptable,
            score=score_promedio,
            razon=razon,
            recomendaciones=recomendaciones,
            metricas={
                'cantidad': len(propiedades),
                'cumplimiento_promedio': score_promedio,
                'nivel_relajacion': nivel_relajacion,
                'score_mejor_propiedad': max(scores_propiedades) if scores_propiedades else 0,
                'score_peor_propiedad': min(scores_propiedades) if scores_propiedades else 0
            }
        )
    
    def _calcular_score_propiedad(
        self, 
        propiedad: Dict[str, Any], 
        criterios: Dict[str, Any]
    ) -> float:
        """Calcula score de cumplimiento de una propiedad."""
        puntos = 0
        total = 0
        
        # Evaluar precio
        if 'precio_max' in criterios and 'precio' in propiedad:
            total += 1
            if propiedad['precio'] <= criterios['precio_max']:
                puntos += 1
            else:
                # Penalización proporcional si se excede
                exceso = (propiedad['precio'] - criterios['precio_max']) / criterios['precio_max']
                puntos += max(0, 1 - exceso)
        
        # Evaluar área
        if 'area_min' in criterios and 'area' in propiedad:
            total += 1
            if propiedad['area'] >= criterios['area_min']:
                puntos += 1
            else:
                # Penalización proporcional si es menor
                deficit = (criterios['area_min'] - propiedad['area']) / criterios['area_min']
                puntos += max(0, 1 - deficit)
        
        # Evaluar tipo de inmueble
        if 'tipo' in criterios and 'tipo' in propiedad:
            total += 1
            if propiedad['tipo'] == criterios['tipo']:
                puntos += 1
        
        # Evaluar habitaciones
        if 'habitaciones_min' in criterios and 'habitaciones' in propiedad:
            total += 1
            if propiedad['habitaciones'] >= criterios['habitaciones_min']:
                puntos += 1
        
        # Evaluar zona (si es preferida)
        if 'zonas_preferidas' in criterios and 'zona' in propiedad:
            total += 1
            if propiedad['zona'] in criterios['zonas_preferidas']:
                puntos += 1
        
        return puntos / total if total > 0 else 0.5
    
    def _calcular_nivel_relajacion(
        self, 
        originales: Dict[str, Any], 
        actuales: Dict[str, Any]
    ) -> float:
        """Calcula qué tanto se han relajado los criterios."""
        if not originales:
            return 0.0
        
        cambios = 0
        total = 0
        
        # Comparar precio
        if 'precio_max' in originales and 'precio_max' in actuales:
            total += 1
            cambio_precio = (
                actuales['precio_max'] - originales['precio_max']
            ) / originales['precio_max']
            cambios += abs(cambio_precio)
        
        # Comparar área
        if 'area_min' in originales and 'area_min' in actuales:
            total += 1
            cambio_area = (
                originales['area_min'] - actuales['area_min']
            ) / originales['area_min']
            cambios += abs(cambio_area)
        
        return cambios / total if total > 0 else 0.0
    
    def _generar_razon_rechazo(
        self, 
        cantidad: int, 
        score: float, 
        cantidad_suficiente: bool
    ) -> str:
        """Genera razón de rechazo de resultados."""
        if cantidad == 0:
            return "No se encontraron propiedades"
        elif not cantidad_suficiente:
            return (
                f"Solo se encontraron {cantidad} propiedades, "
                f"se requieren al menos {self.min_propiedades}"
            )
        else:
            return (
                f"Score promedio ({score:.2f}) por debajo del "
                f"mínimo aceptable ({self.score_minimo})"
            )
    
    def _generar_recomendaciones(
        self, 
        propiedades: List[Dict[str, Any]], 
        criterios: Dict[str, Any]
    ) -> List[str]:
        """Genera recomendaciones para relajación."""
        recomendaciones = []
        
        if not propiedades:
            if 'precio_max' in criterios:
                recomendaciones.append("Incrementar el presupuesto máximo")
            if 'area_min' in criterios:
                recomendaciones.append("Reducir el área mínima requerida")
            if 'zonas_preferidas' in criterios:
                recomendaciones.append("Ampliar las zonas de búsqueda")
        else:
            # Analizar por qué las propiedades no cumplen
            precios_altos = sum(
                1 for p in propiedades 
                if p.get('precio', 0) > criterios.get('precio_max', float('inf'))
            )
            if precios_altos > len(propiedades) / 2:
                recomendaciones.append("Aumentar presupuesto (muchas opciones superan el máximo)")
        
        return recomendaciones


def evaluar_resultados(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo del grafo: evalúa los resultados actuales.
    
    Args:
        state: Estado actual del sistema
        
    Returns:
        Estado actualizado con evaluación
    """
    evaluador = EvaluadorResultados()
    evaluacion = evaluador.evaluar(state)
    
    return {
        **state,
        'evaluacion': {
            'es_aceptable': evaluacion.es_aceptable,
            'score': evaluacion.score,
            'razon': evaluacion.razon,
            'recomendaciones': evaluacion.recomendaciones,
            'metricas': evaluacion.metricas
        }
    }