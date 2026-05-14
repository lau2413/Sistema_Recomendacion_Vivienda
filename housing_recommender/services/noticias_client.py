from __future__ import annotations

from typing import Any, Protocol


class NoticiasClient(Protocol):
    def consultar(self, ubicaciones: list[str]) -> list[dict[str, Any]]:
        ...


class MockNoticiasClient:
    def consultar(self, ubicaciones: list[str]) -> list[dict[str, Any]]:
        ubicaciones_normalizadas = {ubicacion.lower() for ubicacion in ubicaciones}
        return [
            noticia
            for noticia in _noticias_demo()
            if not ubicaciones_normalizadas
            or noticia["ubicacion"].lower() in ubicaciones_normalizadas
        ]


def obtener_noticias(
    ubicaciones: list[str],
    client: NoticiasClient | None = None,
) -> list[dict[str, Any]]:
    proveedor = client or MockNoticiasClient()
    return [
        {
            "fuente": noticia["fuente"],
            "texto": noticia["texto"],
            "resumen": noticia["resumen"],
        }
        for noticia in proveedor.consultar(ubicaciones)
    ]


def _noticias_demo() -> list[dict[str, Any]]:
    return [
        {
            "ubicacion": "Norte",
            "fuente": "mock_contexto_urbano",
            "texto": "Zona norte en valorizacion por nuevos proyectos de transporte.",
            "resumen": "Valorizacion y mejora de movilidad en el norte.",
        },
        {
            "ubicacion": "Sur",
            "fuente": "mock_contexto_urbano",
            "texto": "Zona sur con alta demanda residencial y buena oferta de servicios.",
            "resumen": "Alta demanda y servicios consolidados en el sur.",
        },
        {
            "ubicacion": "Centro",
            "fuente": "mock_contexto_urbano",
            "texto": "Centro con proyectos de renovacion urbana en desarrollo.",
            "resumen": "Renovacion urbana con posibles cambios de valorizacion.",
        },
    ]
