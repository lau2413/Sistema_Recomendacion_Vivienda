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
            or _ubicacion_coincide(noticia["ubicacion"], ubicaciones_normalizadas)
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
            "ubicacion": "El Poblado",
            "fuente": "mock_contexto_urbano",
            "texto": "El Poblado mantiene alta valorizacion y buena oferta de servicios, aunque con precios superiores al promedio.",
            "resumen": "Alta valorizacion, servicios consolidados y precios altos.",
        },
        {
            "ubicacion": "Laureles",
            "fuente": "mock_contexto_urbano",
            "texto": "Laureles presenta buena conectividad, comercio barrial y demanda residencial estable.",
            "resumen": "Zona equilibrada por movilidad, servicios y demanda familiar.",
        },
        {
            "ubicacion": "Envigado",
            "fuente": "mock_contexto_urbano",
            "texto": "Envigado conserva atractivo para familias por oferta educativa, seguridad percibida y disponibilidad de casas.",
            "resumen": "Contexto favorable para familias y casas de mayor area.",
        },
        {
            "ubicacion": "Belen",
            "fuente": "mock_contexto_urbano",
            "texto": "Belen combina precios medios, buena oferta de apartamentos y acceso a corredores de transporte.",
            "resumen": "Alternativa de precio medio con oferta residencial amplia.",
        },
        {
            "ubicacion": "Sabaneta",
            "fuente": "mock_contexto_urbano",
            "texto": "Sabaneta tiene crecimiento residencial activo y oferta competitiva para apartamentos familiares.",
            "resumen": "Crecimiento residencial con precios competitivos.",
        },
        {
            "ubicacion": "Centro",
            "fuente": "mock_contexto_urbano",
            "texto": "El Centro cuenta con renovacion urbana y precios menores, pero con mayor variabilidad del entorno.",
            "resumen": "Precios bajos y renovacion urbana con mayor incertidumbre.",
        },
        {
            "ubicacion": "Robledo",
            "fuente": "mock_contexto_urbano",
            "texto": "Robledo ofrece precios accesibles y oferta residencial en expansion en sectores conectados.",
            "resumen": "Opcion accesible con oferta residencial en expansion.",
        },
    ]


def _ubicacion_coincide(ubicacion_noticia: str, ubicaciones: set[str]) -> bool:
    noticia = ubicacion_noticia.lower()
    equivalencias = {
        "sur": {"envigado", "sabaneta"},
        "norte": {"robledo"},
        "occidente": {"laureles", "belen", "robledo"},
        "poblado": {"el poblado"},
    }

    if noticia in ubicaciones:
        return True

    return any(noticia in equivalencias.get(ubicacion, set()) for ubicacion in ubicaciones)
