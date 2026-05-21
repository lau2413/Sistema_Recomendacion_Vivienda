"""Ejemplos de ejecucion del sistema con casos exitosos y restrictivos."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from housing_recommender.main import ejecutar_sistema


def ejemplo_texto_libre():
    """Caso principal: el usuario expresa preferencias en lenguaje natural."""

    print("\n" + "=" * 80)
    print("--EJEMPLO 1: Texto libre con resultados esperados--")
    print("=" * 80)

    texto = (
        "Busco apartamento  con 2 habitaciones, 3 baños "
        "y al menos 90 metros cuadrados.."
    )
    return ejecutar_sistema(texto)


def ejemplo_caso_ideal():
    """Caso estructurado donde los criterios iniciales encuentran resultados."""

    print("\n" + "=" * 80)
    print("--EJEMPLO 2: Criterios estructurados alcanzables--")
    print("=" * 80)

    criterios = {
        "precio_max": 540_000_000,
        "habitaciones": 2,
        "tipo": "apartamento",
    }
    return ejecutar_sistema(criterios)


def ejemplo_caso_restrictivo():
    """Caso con criterios muy restrictivos que requiere relajacion."""

    print("\n" + "=" * 80)
    print("--EJEMPLO 3: Criterios restrictivos con relajacion--")
    print("=" * 80)

    criterios = {
        "precio_max": 150_000_000,
        "area_min": 120,
        "habitaciones": 4,
        "tipo": "apartamento",
        "ubicacion": "El Poblado",
    }
    return ejecutar_sistema(criterios)


def ejecutar_todos_ejemplos() -> None:
    """Ejecuta todos los ejemplos de demostracion."""

    print("\n" + "#" * 80)
    print("# DEMOSTRACION DEL SISTEMA DE RECOMENDACION DE VIVIENDAS")
    print("#" * 80)

    ejemplos = [
        ("Texto libre", ejemplo_texto_libre),
        ("Caso ideal", ejemplo_caso_ideal),
        ("Caso restrictivo", ejemplo_caso_restrictivo),
    ]
    resultados = {}

    for nombre, funcion_ejemplo in ejemplos:
        try:
            resultados[nombre] = funcion_ejemplo()
            input("\nPresiona Enter para continuar con el siguiente ejemplo...")
        except EOFError:
            continue
        except Exception as exc:
            print(f"\nError en {nombre}: {exc}")

    print("\n" + "#" * 80)
    print("# RESUMEN COMPARATIVO")
    print("#" * 80 + "\n")

    for nombre, resultado in resultados.items():
        evaluacion = resultado.get("evaluacion") or {}
        print(f"{nombre}:")
        print(f"  - Iteraciones de relajacion: {resultado.get('iteracion', 0)}")
        print(f"  - Propiedades filtradas: {len(resultado.get('propiedades_filtradas') or [])}")
        print(f"  - Recomendaciones finales: {len(resultado.get('recomendaciones_finales') or [])}")
        print(f"  - Score evaluador: {evaluacion.get('score', 0):.2f}/10")
        print()


if __name__ == "__main__":
    ejecutar_todos_ejemplos()
