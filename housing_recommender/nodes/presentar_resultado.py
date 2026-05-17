"""
Módulo de presentación de resultados finales.
Genera recomendaciones explicadas y calcula scores de cumplimiento.
"""

from typing import Dict, List, Any, Tuple


def generar_recomendaciones(
    state: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Genera las recomendaciones finales con explicaciones.
    
    Args:
        state: Estado final del sistema
        
    Returns:
        Tupla (recomendaciones, explicaciones)
    """
    propiedades = state.get('propiedades_filtradas', [])
    criterios_originales = state.get('criterios_originales', {})
    criterios_actuales = state.get('criterios_actuales', {})
    evaluacion = state.get('evaluacion', {})
    
    recomendaciones = []
    
    for prop in propiedades:
        recomendacion = {
            'propiedad': prop,
            'score': _calcular_score_individual(prop, criterios_actuales),
            'explicacion': _generar_explicacion(
                prop, 
                criterios_originales, 
                criterios_actuales
            ),
            'cumplimiento': _analizar_cumplimiento(prop, criterios_originales)
        }
        recomendaciones.append(recomendacion)
    
    # Ordenar por score
    recomendaciones.sort(key=lambda x: x['score'], reverse=True)
    
    # Generar explicaciones generales
    explicaciones = _generar_explicaciones_generales(
        state, 
        recomendaciones
    )
    
    return recomendaciones, explicaciones


def _calcular_score_individual(
    propiedad: Dict[str, Any], 
    criterios: Dict[str, Any]
) -> float:
    """Calcula score de una propiedad."""
    puntos = 0
    total = 0
    
    if 'precio_max' in criterios and 'precio' in propiedad:
        total += 1
        if propiedad['precio'] <= criterios['precio_max']:
            puntos += 1
    
    if 'area_min' in criterios and 'area' in propiedad:
        total += 1
        if propiedad['area'] >= criterios['area_min']:
            puntos += 1
    
    if 'habitaciones_min' in criterios and 'habitaciones' in propiedad:
        total += 1
        if propiedad['habitaciones'] >= criterios['habitaciones_min']:
            puntos += 1
    
    return puntos / total if total > 0 else 0.0


def _generar_explicacion(
    propiedad: Dict[str, Any],
    criterios_orig: Dict[str, Any],
    criterios_act: Dict[str, Any]
) -> str:
    """Genera explicación de por qué se recomienda una propiedad."""
    razones = []
    
    # Analizar precio
    if 'precio' in propiedad and 'precio_max' in criterios_act:
        if propiedad['precio'] <= criterios_orig.get('precio_max', float('inf')):
            razones.append(f"Dentro del presupuesto original (${propiedad['precio']:,})")
        elif propiedad['precio'] <= criterios_act['precio_max']:
            razones.append(
                f"Dentro del presupuesto ajustado "
                f"(${propiedad['precio']:,} de ${criterios_act['precio_max']:,})"
            )
    
    # Analizar área
    if 'area' in propiedad and 'area_min' in criterios_act:
        if propiedad['area'] >= criterios_orig.get('area_min', 0):
            razones.append(f"Cumple área original ({propiedad['area']}m²)")
        elif propiedad['area'] >= criterios_act['area_min']:
            razones.append(f"Cumple área ajustada ({propiedad['area']}m²)")
    
    # Zona
    if 'zona' in propiedad:
        razones.append(f"Ubicada en {propiedad['zona']}")
    
    return ". ".join(razones) if razones else "Mejor opción disponible"


def _analizar_cumplimiento(
    propiedad: Dict[str, Any],
    criterios_originales: Dict[str, Any]
) -> Dict[str, bool]:
    """Analiza qué criterios originales cumple la propiedad."""
    cumplimiento = {}
    
    if 'precio_max' in criterios_originales and 'precio' in propiedad:
        cumplimiento['precio'] = propiedad['precio'] <= criterios_originales['precio_max']
    
    if 'area_min' in criterios_originales and 'area' in propiedad:
        cumplimiento['area'] = propiedad['area'] >= criterios_originales['area_min']
    
    if 'habitaciones_min' in criterios_originales and 'habitaciones' in propiedad:
        cumplimiento['habitaciones'] = (
            propiedad['habitaciones'] >= criterios_originales['habitaciones_min']
        )
    
    return cumplimiento


def _generar_explicaciones_generales(
    state: Dict[str, Any],
    recomendaciones: List[Dict[str, Any]]
) -> List[str]:
    """Genera explicaciones del proceso completo."""
    explicaciones = []
    
    # Resumen de búsqueda
    num_propiedades = len(recomendaciones)
    explicaciones.append(
        f"Se encontraron {num_propiedades} propiedades que cumplen los criterios"
    )
    
    # Modificaciones realizadas
    historial = state.get('historial_relajacion', [])
    if historial:
        explicaciones.append(
            f"Se realizaron {len(historial)} ajustes a los criterios iniciales:"
        )
        for entrada in historial:
            cambios = entrada.get('cambios', [])
            for cambio in cambios:
                explicaciones.append(f"  - {cambio}")
    else:
        explicaciones.append("Los criterios originales no fueron modificados")
    
    # Score promedio
    if recomendaciones:
        score_prom = sum(r['score'] for r in recomendaciones) / len(recomendaciones)
        explicaciones.append(
            f"Score promedio de cumplimiento: {score_prom:.1%}"
        )
    
    return explicaciones


def presentar_resultados(state: Dict[str, Any]) -> None:
    """
    Presenta los resultados finales al usuario.
    
    Args:
        state: Estado final del sistema
    """
    print("\n" + "="*80)
    print("RESULTADOS DE LA BÚSQUEDA DE VIVIENDA")
    print("="*80 + "\n")
    
    recomendaciones, explicaciones = generar_recomendaciones(state)
    
    # Mostrar explicaciones generales
    print("RESUMEN DEL PROCESO:")
    print("-" * 80)
    for exp in explicaciones:
        print(exp)
    print()
    
    # Mostrar recomendaciones
    if recomendaciones:
        print("\nPROPIEDADES RECOMENDADAS:")
        print("-" * 80)
        for i, rec in enumerate(recomendaciones, 1):
            prop = rec['propiedad']
            print(f"\n{i}. Propiedad en {prop.get('zona', 'N/A')}")
            print(f"   Precio: ${prop.get('precio', 0):,}")
            print(f"   Área: {prop.get('area', 0)}m²")
            print(f"   Habitaciones: {prop.get('habitaciones', 0)}")
            print(f"   Score: {rec['score']:.1%}")
            print(f"   Explicación: {rec['explicacion']}")
            
            cumplimiento = rec['cumplimiento']
            print(f"   Cumplimiento de criterios originales:")
            for criterio, cumple in cumplimiento.items():
                estado = "✅" if cumple else "❌"
                print(f"     {estado} {criterio}")
    else:
        print("\nNo se encontraron propiedades que cumplan los criterios")
        print("Considere ajustar sus preferencias")
    
    print("\n" + "="*80)