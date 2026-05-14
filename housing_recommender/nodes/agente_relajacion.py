# agente_relajacion.py
"""
Módulo de relajación progresiva de criterios.
Modifica los criterios de búsqueda cuando no se encuentran resultados satisfactorios.
"""

from typing import Dict, List, Any
from copy import deepcopy
import math


class AgenteRelajacion:
    """
    Implementa la estrategia de relajación progresiva de criterios.
    Modifica las condiciones de búsqueda de forma controlada y gradual.
    """
    
    def __init__(
        self, 
        factor_precio: float = 0.10,
        factor_area: float = 0.10,
        max_relajaciones: int = 5
    ):
        """
        Args:
            factor_precio: Porcentaje de incremento en precio por iteración
            factor_area: Porcentaje de reducción en área por iteración
            max_relajaciones: Número máximo de relajaciones permitidas
        """
        self.factor_precio = factor_precio
        self.factor_area = factor_area
        self.max_relajaciones = max_relajaciones
        
        # Prioridad de relajación (qué relajar primero)
        self.estrategia_relajacion = [
            'precio',
            'area',
            'habitaciones',
            'zonas',
            'tipo'
        ]
    
    def relajar_criterios(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Relaja los criterios de búsqueda basándose en el estado actual.
        
        Args:
            state: Estado actual del sistema
            
        Returns:
            Estado actualizado con criterios relajados
        """
        iteracion_actual = state.get('iteracion_relajacion', 0)
        
        if iteracion_actual >= self.max_relajaciones:
            return {
                **state,
                'relajacion_completa': True,
                'mensaje_relajacion': "Se alcanzó el límite máximo de relajaciones"
            }
        
        criterios_actuales = deepcopy(state.get('criterios_actuales', {}))
        historial_relajacion = state.get('historial_relajacion', [])
        
        # Determinar qué criterio relajar basado en la iteración
        cambios_realizados = []
        
        # Estrategia adaptativa basada en recomendaciones del evaluador
        recomendaciones = state.get('evaluacion', {}).get('recomendaciones', [])
        
        if recomendaciones:
            cambios = self._aplicar_recomendaciones(
                criterios_actuales, 
                recomendaciones
            )
            cambios_realizados.extend(cambios)
        else:
            # Estrategia por defecto: relajar según prioridad
            cambios = self._aplicar_estrategia_default(
                criterios_actuales, 
                iteracion_actual
            )
            cambios_realizados.extend(cambios)
        
        # Registrar cambios en historial
        registro_relajacion = {
            'iteracion': iteracion_actual + 1,
            'cambios': cambios_realizados,
            'criterios_antes': state.get('criterios_actuales', {}),
            'criterios_despues': criterios_actuales
        }
        historial_relajacion.append(registro_relajacion)
        
        return {
            **state,
            'criterios_actuales': criterios_actuales,
            'iteracion_relajacion': iteracion_actual + 1,
            'historial_relajacion': historial_relajacion,
            'mensaje_relajacion': self._generar_mensaje_relajacion(cambios_realizados)
        }
    
    def _aplicar_recomendaciones(
        self, 
        criterios: Dict[str, Any], 
        recomendaciones: List[str]
    ) -> List[str]:
        """Aplica relajaciones basadas en recomendaciones del evaluador."""
        cambios = []
        
        for rec in recomendaciones:
            rec_lower = rec.lower()
            
            if 'presupuesto' in rec_lower or 'precio' in rec_lower:
                cambio = self._relajar_precio(criterios)
                if cambio:
                    cambios.append(cambio)
            
            if 'área' in rec_lower or 'area' in rec_lower:
                cambio = self._relajar_area(criterios)
                if cambio:
                    cambios.append(cambio)
            
            if 'zona' in rec_lower:
                cambio = self._relajar_zonas(criterios)
                if cambio:
                    cambios.append(cambio)
        
        return cambios
    
    def _aplicar_estrategia_default(
        self, 
        criterios: Dict[str, Any], 
        iteracion: int
    ) -> List[str]:
        """Aplica estrategia de relajación por defecto."""
        cambios = []
        
        # Determinar qué relajar según la iteración
        if iteracion % 3 == 0:  # Iteraciones 0, 3, 6...
            cambio = self._relajar_precio(criterios)
            if cambio:
                cambios.append(cambio)
        
        elif iteracion % 3 == 1:  # Iteraciones 1, 4, 7...
            cambio = self._relajar_area(criterios)
            if cambio:
                cambios.append(cambio)
        
        else:  # Iteraciones 2, 5, 8...
            cambio = self._relajar_habitaciones(criterios)
            if cambio:
                cambios.append(cambio)
            cambio = self._relajar_zonas(criterios)
            if cambio:
                cambios.append(cambio)
        
        return cambios
    
    def _relajar_precio(self, criterios: Dict[str, Any]) -> str:
        """Incrementa el precio máximo."""
        if 'precio_max' in criterios:
            precio_anterior = criterios['precio_max']
            criterios['precio_max'] = int(precio_anterior * (1 + self.factor_precio))
            return (
                f"Precio máximo incrementado de ${precio_anterior:,} "
                f"a ${criterios['precio_max']:,} "
                f"(+{self.factor_precio*100:.0f}%)"
            )
        return ""
    
    def _relajar_area(self, criterios: Dict[str, Any]) -> str:
        """Reduce el área mínima."""
        if 'area_min' in criterios:
            area_anterior = criterios['area_min']
            criterios['area_min'] = int(area_anterior * (1 - self.factor_area))
            return (
                f"Área mínima reducida de {area_anterior}m² "
                f"a {criterios['area_min']}m² "
                f"(-{self.factor_area*100:.0f}%)"
            )
        return ""
    
    def _relajar_habitaciones(self, criterios: Dict[str, Any]) -> str:
        """Reduce número mínimo de habitaciones."""
        if 'habitaciones_min' in criterios and criterios['habitaciones_min'] > 1:
            hab_anterior = criterios['habitaciones_min']
            criterios['habitaciones_min'] -= 1
            return (
                f"Habitaciones mínimas reducidas de {hab_anterior} "
                f"a {criterios['habitaciones_min']}"
            )
        return ""
    
    def _relajar_zonas(self, criterios: Dict[str, Any]) -> str:
        """Amplía las zonas de búsqueda."""
        if 'zonas_preferidas' in criterios:
            zonas_actuales = len(criterios['zonas_preferidas'])
            # Esto requeriría acceso a todas las zonas disponibles
            # Por ahora, solo indicamos la intención
            return f"Ampliando zonas de búsqueda (actualmente {zonas_actuales} zonas)"
        return ""
    
    def _generar_mensaje_relajacion(self, cambios: List[str]) -> str:
        """Genera mensaje descriptivo de los cambios realizados."""
        if not cambios:
            return "No se realizaron cambios en los criterios"
        
        return "Criterios relajados: " + "; ".join(cambios)


def relajar_condiciones(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo del grafo: relaja las condiciones de búsqueda.
    
    Args:
        state: Estado actual del sistema
        
    Returns:
        Estado actualizado con criterios relajados
    """
    agente = AgenteRelajacion()
    return agente.relajar_criterios(state)