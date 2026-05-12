"""
nodes/agente_noticias.py  — Nodo ③ (corre en paralelo con propiedades_scraping)
Responsabilidad: buscar noticias recientes sobre las zonas identificadas.
Produce: {"contexto_noticias": [...]}
"""
from __future__ import annotations

from config.settings import settings
from services.noticias_client import buscar_noticias_zona, mock_noticias
from state.models import EstadoSistema


async def agente_noticias(estado: EstadoSistema) -> dict:
    criterios = estado.criterios_actuales
    barrios = [z.nombre for z in estado.zonas_relevantes]

    if settings.use_mock_scraping:
        noticias = mock_noticias(barrios)
    else:
        noticias = await buscar_noticias_zona(
            ciudad=criterios.ciudad,
            barrios=barrios,
            max_por_barrio=3,
        )

    return {"contexto_noticias": noticias}