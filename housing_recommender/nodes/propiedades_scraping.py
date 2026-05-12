"""
nodes/propiedades_scraping.py  — Nodo ⑤ (corre en paralelo con agente_noticias)
Responsabilidad: buscar propiedades en Finca Raíz según criterios_actuales.
Produce: {"propiedades_raw": [...]}
"""
from __future__ import annotations

from config.settings import settings
from services.scraping_client import buscar_propiedades, mock_propiedades
from state.models import EstadoSistema


async def propiedades_scraping(estado: EstadoSistema) -> dict:
    criterios = estado.criterios_actuales

    if settings.use_mock_scraping:
        propiedades = mock_propiedades(criterios, n=8)
    else:
        propiedades = await buscar_propiedades(
            criterios=criterios,
            paginas=settings.max_paginas_scraping,
        )

    return {"propiedades_raw": propiedades}