"""
Punto de entrada principal del sistema de recomendación de viviendas.
Ejecuta el grafo completo con los criterios del usuario.
"""

from housing_recommender.graph.builder import construir_grafo
from housing_recommender.nodes.presentar_resultado import presentar_resultados


def ejecutar_sistema(criterios_usuario: dict):
    """
    Ejecuta el sistema completo de recomendación.
    
    Args:
        criterios_usuario: Diccionario con preferencias del usuario
        
    Returns:
        Estado final del sistema
    """
    print("\n" + "="*80)
    print("--SISTEMA DE RECOMENDACIÓN DE VIVIENDAS--")
    print("="*80 + "\n")
    
    # Construir el grafo
    print("Construyendo grafo de decisión...")
    app = construir_grafo()
    
    # Estado inicial
    estado_inicial = {
        'criterios_originales': criterios_usuario,
        'criterios_actuales': criterios_usuario.copy(),
        'zonas_analizadas': [],
        'zonas_seleccionadas': [],
        'propiedades_encontradas': [],
        'propiedades_filtradas': [],
        'evaluacion': {},
        'historial_relajacion': [],
        'iteracion_relajacion': 0,
        'relajacion_completa': False,
        'diagnostico': '',
        'mensaje_relajacion': '',
        'recomendaciones_finales': [],
        'explicaciones': []
    }
    
    # Ejecutar el grafo
    print("\nIniciando búsqueda de vivienda...")
    print(f"Criterios iniciales:")
    for key, value in criterios_usuario.items():
        if isinstance(value, list):
            print(f"  - {key}: {', '.join(map(str, value))}")
        elif isinstance(value, (int, float)) and value > 1000:
            print(f"  - {key}: ${value:,}")
        else:
            print(f"  - {key}: {value}")
    
    print("\n" + "-"*80)
    print("--EJECUTANDO FLUJO DEL GRAFO: --")
    print("-"*80)
    
    resultado = app.invoke(estado_inicial)
    
    # Presentar resultados
    print("\n" + "-"*80)
    presentar_resultados(resultado)
    
    return resultado


if __name__ == "__main__":
    # Ejemplo de uso
    criterios_ejemplo = {
        'precio_max': 300_000_000,  # COP
        'area_min': 70,  # m2
        'habitaciones_min': 2,
        'tipo': 'apartamento',
        'zonas_preferidas': ['El Poblado', 'Laureles']
    }
    
    resultado_final = ejecutar_sistema(criterios_ejemplo)