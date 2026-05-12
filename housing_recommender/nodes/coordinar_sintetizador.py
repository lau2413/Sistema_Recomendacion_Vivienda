"""
nodes/coordinar_sintetizador.py  — Nodo ②
Responsabilidad: dado los criterios_actuales, identificar qué zonas/barrios
de la ciudad son candidatos y preparar el estado para los nodos paralelos.
Produce: {"zonas_relevantes": [...]}
"""
from __future__ import annotations

import json

from services.llm_client import llamar_llm
from state.models import EstadoSistema, ZonaInfo

ZONAS_MEDELLIN = {
    "El Poblado": ZonaInfo(nombre="El Poblado", estrato_promedio=6, seguridad_score=8.5, acceso_transporte="Metro + buses"),
    "Laureles": ZonaInfo(nombre="Laureles", estrato_promedio=5, seguridad_score=8.0, acceso_transporte="Metro + buses"),
    "Envigado": ZonaInfo(nombre="Envigado", estrato_promedio=5, seguridad_score=8.2, acceso_transporte="Metro"),
    "Sabaneta": ZonaInfo(nombre="Sabaneta", estrato_promedio=4, seguridad_score=7.8, acceso_transporte="Metro"),
    "Bello": ZonaInfo(nombre="Bello", estrato_promedio=3, seguridad_score=6.5, acceso_transporte="Metro"),
    "Itagüí": ZonaInfo(nombre="Itagüí", estrato_promedio=3, seguridad_score=7.0, acceso_transporte="Metro"),
    "Robledo": ZonaInfo(nombre="Robledo", estrato_promedio=3, seguridad_score=6.8, acceso_transporte="Metro + cable"),
    "Aranjuez": ZonaInfo(nombre="Aranjuez", estrato_promedio=3, seguridad_score=6.5, acceso_transporte="Metro"),
    "La América": ZonaInfo(nombre="La América", estrato_promedio=4, seguridad_score=7.2, acceso_transporte="Metro"),
    "Belén": ZonaInfo(nombre="Belén", estrato_promedio=4, seguridad_score=7.5, acceso_transporte="Metro"),
}

SISTEMA_PROMPT = """
Eres un experto en el mercado inmobiliario de ciudades colombianas.
Dado un conjunto de criterios de búsqueda, sugiere entre 3 y 6 zonas o barrios
donde es razonable buscar vivienda. Devuelve SOLO una lista JSON de nombres de barrio.
Ejemplo: ["El Poblado", "Laureles", "Envigado"]
"""


async def coordinar_sintetizador(estado: EstadoSistema) -> dict:
    criterios = estado.criterios_actuales
    ciudad = criterios.ciudad

    # Si el usuario ya indicó barrios, usarlos; si no, preguntar al LLM
    if criterios.barrios_preferidos:
        nombres_zonas = criterios.barrios_preferidos
    else:
        prompt_usuario = (
            f"Ciudad: {ciudad}\n"
            f"Tipo de inmueble: {criterios.tipo_inmueble}\n"
            f"Modalidad: {criterios.modalidad}\n"
            f"Presupuesto máximo: {criterios.precio_max or 'no especificado'} COP\n"
            f"Área mínima: {criterios.area_min or 'no especificada'} m²\n"
            f"¿Qué barrios recomiendas buscar?"
        )
        respuesta = await llamar_llm(sistema=SISTEMA_PROMPT, usuario=prompt_usuario)
        nombres_zonas = _extraer_lista(respuesta)

    # Enriquecer con información conocida (ciudad de Medellín) o crear ZonaInfo básica
    zonas: list[ZonaInfo] = []
    for nombre in nombres_zonas:
        zona = ZONAS_MEDELLIN.get(nombre)
        if zona:
            zonas.append(zona)
        else:
            zonas.append(ZonaInfo(nombre=nombre))

    return {"zonas_relevantes": zonas}


def _extraer_lista(texto: str) -> list[str]:
    """Extrae la primera lista JSON del texto."""
    import re
    match = re.search(r"\[.*?\]", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    # Fallback: split por comas
    return [s.strip().strip('"') for s in texto.split(",") if s.strip()]