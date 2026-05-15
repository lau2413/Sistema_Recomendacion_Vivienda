"""
Ejemplos de ejecución del sistema con diferentes casos de uso.
Demuestra el comportamiento del sistema bajo distintos escenarios.
"""

import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from housing_recommender.main import ejecutar_sistema


def ejemplo_caso_ideal():
    """Caso donde los criterios iniciales encuentran resultados."""
    print("\n" + "="*80)
    print("--EJEMPLO 1: Caso ideal - Criterios alcanzables--")
    print("="*80)
    
    criterios = {
        'precio_max': 400_000_000,
        'area_min': 60,
        'habitaciones_min': 2,
        'tipo': 'apartamento',
        'zonas_preferidas': ['El Poblado', 'Laureles', 'Envigado']
    }
    
    resultado = ejecutar_sistema(criterios)
    return resultado


def ejemplo_caso_restrictivo():
    """Caso con criterios muy restrictivos que requieren relajación."""
    print("\n" + "="*80)
    print("--EJEMPLO 2: Criterios restrictivos - Requiere relajación--")
    print("="*80)
    
    criterios = {
        'precio_max': 150_000_000,
        'area_min': 120,
        'habitaciones_min': 4,
        'tipo': 'apartamento',
        'zonas_preferidas': ['El Poblado']
    }
    
    resultado = ejecutar_sistema(criterios)
    return resultado


def ejemplo_presupuesto_medio():
    """Caso con presupuesto medio y criterios balanceados."""
    print("\n" + "="*80)
    print("--EJEMPLO 3: Presupuesto medio - Búsqueda balanceada--")
    print("="*80)
    
    criterios = {
        'precio_max': 250_000_000,
        'area_min': 75,
        'habitaciones_min': 3,
        'tipo': 'apartamento',
        'zonas_preferidas': ['Laureles', 'Estadio', 'Belén']
    }
    
    resultado = ejecutar_sistema(criterios)
    return resultado


def ejecutar_todos_ejemplos():
    """Ejecuta todos los ejemplos de demostración."""
    print("\n" + "#"*80)
    print("# DEMOSTRACIÓN DEL SISTEMA DE RECOMENDACIÓN DE VIVIENDAS")
    print("#"*80)
    
    ejemplos = [
        ("Caso Ideal", ejemplo_caso_ideal),
        ("Caso Restrictivo", ejemplo_caso_restrictivo),
        ("Presupuesto Medio", ejemplo_presupuesto_medio),
    ]
    
    resultados = {}
    
    for nombre, funcion_ejemplo in ejemplos:
        try:
            resultado = funcion_ejemplo()
            resultados[nombre] = resultado
            input("\nPresiona Enter para continuar con el siguiente ejemplo...")
        except Exception as e:
            print(f"\nError en {nombre}: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumen comparativo
    print("\n" + "#"*80)
    print("# RESUMEN COMPARATIVO")
    print("#"*80 + "\n")
    
    for nombre, resultado in resultados.items():
        iteraciones = resultado.get('iteracion_relajacion', 0)
        num_propiedades = len(resultado.get('propiedades_filtradas', []))
        score = resultado.get('evaluacion', {}).get('score', 0)
        
        print(f"{nombre}:")
        print(f"  - Iteraciones de relajación: {iteraciones}")
        print(f"  - Propiedades encontradas: {num_propiedades}")
        print(f"  - Score promedio: {score:.1%}")
        print()


if __name__ == "__main__":
    ejecutar_todos_ejemplos()