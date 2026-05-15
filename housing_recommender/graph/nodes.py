"""
Implementación de los nodos del grafo.
Cada función representa una actividad del sistema.
"""

from typing import Dict, Any


def interpretar_requisitos(state: Dict[str, Any]) -> Dict[str, Any]:
    """Interpreta y estructura los requerimientos del usuario."""
    print("Interpretando requisitos del usuario...")
    
    return {
        **state,
        'criterios_actuales': state.get('criterios_originales', {}).copy(),
        'iteracion_relajacion': 0,
        'historial_relajacion': [],
        'relajacion_completa': False
    }


def identificar_zonas(state: Dict[str, Any]) -> Dict[str, Any]:
    """Identifica zonas relevantes según criterios."""
    print("Identificando zonas relevantes...")
    
    # Zonas de Medellín
    todas_zonas = [
        "El Poblado", "Laureles", "Envigado", "Sabaneta", 
        "Estadio", "Belén", "La América", "Itagüí"
    ]
    
    # Si el usuario especificó zonas, usar esas; si no, usar todas
    zonas_preferidas = state.get('criterios_actuales', {}).get('zonas_preferidas', [])
    
    if zonas_preferidas:
        zonas_analizar = zonas_preferidas
    else:
        zonas_analizar = todas_zonas[:5]  # Tomar las primeras 5
    
    print(f"     Zonas a analizar: {', '.join(zonas_analizar)}")
    
    return {
        **state,
        'zonas_analizadas': zonas_analizar
    }


def evaluar_zonas(state: Dict[str, Any]) -> Dict[str, Any]:
    """Evalúa las zonas identificadas."""
    print("Evaluando zonas...")
    
    zonas = state.get('zonas_analizadas', [])
    # Seleccionar las mejores zonas (simplificado)
    zonas_seleccionadas = zonas[:3] if len(zonas) > 3 else zonas
    
    print(f"     Zonas seleccionadas: {', '.join(zonas_seleccionadas)}")
    
    return {
        **state,
        'zonas_seleccionadas': zonas_seleccionadas
    }


def buscar_propiedades(state: Dict[str, Any]) -> Dict[str, Any]:
    """Busca propiedades en las zonas seleccionadas."""
    print("Buscando propiedades...")
    
    criterios = state.get('criterios_actuales', {})
    zonas = state.get('zonas_seleccionadas', [])
    
    # Simulación de búsqueda de propiedades
    # En un sistema real, ACÁ SE CONSULTA A LA API O LA BD DE PROPIEDADES
    propiedades_simuladas = []
    
    for i, zona in enumerate(zonas):
        # Generar 1-2 propiedades por zona
        for j in range(2):
            precio_base = criterios.get('precio_max', 300_000_000)
            area_base = criterios.get('area_min', 70)
            
            # Variar un poco los valores
            import random
            factor = random.uniform(0.8, 1.2)
            
            propiedad = {
                'id': len(propiedades_simuladas) + 1,
                'zona': zona,
                'precio': int(precio_base * factor),
                'area': int(area_base * random.uniform(0.9, 1.3)),
                'habitaciones': criterios.get('habitaciones_min', 2) + random.randint(-1, 1),
                'tipo': criterios.get('tipo', 'apartamento'),
                'direccion': f"Calle {random.randint(1, 100)} #{random.randint(1, 50)}-{random.randint(1, 99)}"
            }
            
            # Asegurar valores mínimos
            propiedad['habitaciones'] = max(1, propiedad['habitaciones'])
            propiedad['area'] = max(30, propiedad['area'])
            
            propiedades_simuladas.append(propiedad)
    
    print(f"     Propiedades encontradas: {len(propiedades_simuladas)}")
    
    return {
        **state,
        'propiedades_encontradas': propiedades_simuladas
    }


def filtrar_propiedades(state: Dict[str, Any]) -> Dict[str, Any]:
    """Filtra propiedades según criterios actuales."""
    print("--Filtrando propiedades...")
    
    propiedades = state.get('propiedades_encontradas', [])
    criterios = state.get('criterios_actuales', {})
    
    filtradas = []
    for prop in propiedades:
        cumple = True
        
        # Filtrar por precio
        if 'precio_max' in criterios:
            if prop.get('precio', 0) > criterios['precio_max']:
                cumple = False
        
        # Filtrar por área
        if 'area_min' in criterios:
            if prop.get('area', 0) < criterios['area_min']:
                cumple = False
        
        # Filtrar por habitaciones
        if 'habitaciones_min' in criterios:
            if prop.get('habitaciones', 0) < criterios['habitaciones_min']:
                cumple = False
        
        # Filtrar por tipo
        if 'tipo' in criterios:
            if prop.get('tipo', '') != criterios['tipo']:
                cumple = False
        
        if cumple:
            filtradas.append(prop)
    
    print(f"     Propiedades que cumplen criterios: {len(filtradas)}")
    
    return {
        **state,
        'propiedades_filtradas': filtradas
    }


def presentar_resultados_nodo(state: Dict[str, Any]) -> Dict[str, Any]:
    """Prepara resultados finales para presentación."""
    print("--Preparando presentación de resultados...")
    
    from housing_recommender.nodes.presentar_resultado import generar_recomendaciones
    
    recomendaciones, explicaciones = generar_recomendaciones(state)
    
    return {
        **state,
        'recomendaciones_finales': recomendaciones,
        'explicaciones': explicaciones
    }