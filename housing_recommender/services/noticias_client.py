from __future__ import annotations

import html
import unicodedata
import xml.etree.ElementTree as ET
from typing import Any, Mapping, Protocol
from urllib.parse import quote_plus

import httpx

from housing_recommender.config.settings import settings


class NoticiasClient(Protocol):
    def consultar(self, ubicaciones: list[str]) -> list[dict[str, Any]]:
        ...


class GoogleNewsRSSClient:
    nombre = "google_rss"

    def consultar(self, ubicaciones: list[str]) -> list[dict[str, Any]]:
        noticias, _diagnostico = self.consultar_con_diagnostico(ubicaciones)
        return noticias

    def consultar_con_diagnostico(
        self,
        ubicaciones: list[str],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        noticias: list[dict[str, Any]] = []
        diagnostico = _crear_diagnostico(self.nombre, ubicaciones)

        for ubicacion in _normalizar_ubicaciones(ubicaciones):
            query = _query_zona(ubicacion)
            url = (
                "https://news.google.com/rss/search?"
                f"q={quote_plus(query)}&hl=es-419&gl=CO&ceid=CO:es-419"
            )
            consulta = {"ubicacion": ubicacion, "query": query, "url": url}
            try:
                response = httpx.get(url, timeout=15, follow_redirects=True)
                response.raise_for_status()
                encontradas = _parsear_google_rss(response.text, ubicacion)
                filtradas = _filtrar_por_ubicacion(encontradas, ubicacion)
                consulta.update(
                    {
                        "status_code": response.status_code,
                        "resultados_crudos": len(encontradas),
                        "resultados_filtrados": len(filtradas),
                    }
                )
                noticias.extend(filtradas)
            except httpx.HTTPError as exc:
                consulta["error"] = str(exc)
            finally:
                diagnostico["consultas"].append(consulta)

        noticias = _limitar_resultados(_deduplicar(noticias))
        diagnostico["total_resultados"] = len(noticias)
        return noticias, diagnostico


class NewsAPIClient:
    nombre = "newsapi"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.news_api_key

    def consultar(self, ubicaciones: list[str]) -> list[dict[str, Any]]:
        noticias, _diagnostico = self.consultar_con_diagnostico(ubicaciones)
        return noticias

    def consultar_con_diagnostico(
        self,
        ubicaciones: list[str],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        diagnostico = _crear_diagnostico(self.nombre, ubicaciones)
        if not self.api_key:
            diagnostico["error"] = "NEWS_API_KEY no esta configurada."
            return [], diagnostico

        noticias: list[dict[str, Any]] = []
        for ubicacion in _normalizar_ubicaciones(ubicaciones):
            query = _query_zona(ubicacion)
            consulta = {"ubicacion": ubicacion, "query": query}
            try:
                response = httpx.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "language": "es",
                        "sortBy": "publishedAt",
                        "pageSize": settings.news_max_resultados,
                    },
                    headers={"X-Api-Key": self.api_key},
                    timeout=15,
                )
                response.raise_for_status()
                articulos = response.json().get("articles", [])
            except httpx.HTTPError as exc:
                consulta["error"] = str(exc)
                diagnostico["consultas"].append(consulta)
                continue

            encontradas = [
                {
                    "ubicacion": ubicacion,
                    "fuente": articulo.get("source", {}).get("name") or "newsapi",
                    "texto": articulo.get("title") or articulo.get("description") or "",
                    "resumen": articulo.get("description") or articulo.get("title") or "",
                }
                for articulo in articulos
                if articulo.get("title") or articulo.get("description")
            ]
            filtradas = _filtrar_por_ubicacion(encontradas, ubicacion)
            consulta.update(
                {
                    "status_code": response.status_code,
                    "resultados_crudos": len(encontradas),
                    "resultados_filtrados": len(filtradas),
                }
            )
            diagnostico["consultas"].append(consulta)
            noticias.extend(filtradas)

        noticias = _limitar_resultados(_deduplicar(noticias))
        diagnostico["total_resultados"] = len(noticias)
        return noticias, diagnostico


class NoticiasMixtasClient:
    nombre = "mixto"

    def consultar(self, ubicaciones: list[str]) -> list[dict[str, Any]]:
        noticias, _diagnostico = self.consultar_con_diagnostico(ubicaciones)
        return noticias

    def consultar_con_diagnostico(
        self,
        ubicaciones: list[str],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        diagnosticos = []
        noticias = []
        for proveedor in (GoogleNewsRSSClient(), NewsAPIClient()):
            encontradas, diagnostico = proveedor.consultar_con_diagnostico(ubicaciones)
            noticias.extend(encontradas)
            diagnosticos.append(diagnostico)

        noticias = _limitar_resultados(_deduplicar(noticias))
        return noticias, {
            "proveedor": self.nombre,
            "ubicaciones": _normalizar_ubicaciones(ubicaciones),
            "total_resultados": len(noticias),
            "proveedores": diagnosticos,
        }


class MockNoticiasClient:
    nombre = "mock"

    def consultar(self, ubicaciones: list[str]) -> list[dict[str, Any]]:
        noticias, _diagnostico = self.consultar_con_diagnostico(ubicaciones)
        return noticias

    def consultar_con_diagnostico(
        self,
        ubicaciones: list[str],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        ubicaciones_normalizadas = {
            _normalizar_texto(ubicacion)
            for ubicacion in _normalizar_ubicaciones(ubicaciones)
        }
        noticias = [
            noticia
            for noticia in _noticias_demo()
            if ubicaciones_normalizadas
            and _ubicacion_coincide(noticia["ubicacion"], ubicaciones_normalizadas)
        ]
        return noticias, {
            "proveedor": self.nombre,
            "ubicaciones": _normalizar_ubicaciones(ubicaciones),
            "total_resultados": len(noticias),
        }


def obtener_noticias(
    ubicaciones: list[str],
    client: NoticiasClient | None = None,
    incluir_diagnostico: bool = False,
) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], dict[str, Any]]:
    proveedor = client or _crear_cliente_por_configuracion()
    noticias, diagnostico = _consultar_con_diagnostico(proveedor, ubicaciones)
    diagnostico["fallback_mock_usado"] = False

    if not noticias and not isinstance(proveedor, MockNoticiasClient):
        diagnostico["motivo_fallback"] = (
            "El proveedor externo no devolvio noticias relacionadas con las zonas consultadas."
        )
        noticias, diagnostico_mock = MockNoticiasClient().consultar_con_diagnostico(ubicaciones)
        diagnostico["fallback_mock_usado"] = bool(noticias)
        diagnostico["fallback_mock"] = diagnostico_mock

    noticias_normalizadas = [
        {
            "ubicacion": noticia.get("ubicacion"),
            "fuente": noticia["fuente"],
            "texto": noticia["texto"],
            "resumen": noticia["resumen"],
            "impacto_score": _calcular_impacto_score(noticia),
        }
        for noticia in noticias
    ][: settings.news_max_resultados]

    if incluir_diagnostico:
        diagnostico["total_entregado"] = len(noticias_normalizadas)
        return noticias_normalizadas, diagnostico

    return noticias_normalizadas


def _consultar_con_diagnostico(
    proveedor: NoticiasClient,
    ubicaciones: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if hasattr(proveedor, "consultar_con_diagnostico"):
        return proveedor.consultar_con_diagnostico(ubicaciones)  # type: ignore[attr-defined]

    noticias = proveedor.consultar(ubicaciones)
    return noticias, {
        "proveedor": proveedor.__class__.__name__,
        "ubicaciones": _normalizar_ubicaciones(ubicaciones),
        "total_resultados": len(noticias),
    }


def _crear_cliente_por_configuracion() -> NoticiasClient:
    if settings.news_provider == "google_rss":
        return GoogleNewsRSSClient()
    if settings.news_provider == "newsapi":
        return NewsAPIClient()
    if settings.news_provider == "mixto":
        return NoticiasMixtasClient()
    return MockNoticiasClient()


def _crear_diagnostico(proveedor: str, ubicaciones: list[str]) -> dict[str, Any]:
    ubicaciones_normalizadas = _normalizar_ubicaciones(ubicaciones)
    diagnostico = {
        "proveedor": proveedor,
        "ubicaciones": ubicaciones_normalizadas,
        "consultas": [],
        "total_resultados": 0,
    }
    if not ubicaciones_normalizadas:
        diagnostico["advertencia"] = (
            "No se consultaron noticias porque no hay una zona o barrio especifico. "
            "Se evita traer noticias generales de Medellin."
        )
    return diagnostico


def _query_zona(ubicacion: str) -> str:
    return (
        f'"{ubicacion}" Medellin '
        "(vivienda OR inmobiliario OR arriendo OR venta OR comercio OR seguridad OR valorizacion)"
    )


def _normalizar_ubicaciones(ubicaciones: list[str]) -> list[str]:
    limpias = []
    for ubicacion in ubicaciones or []:
        ubicacion_limpia = str(ubicacion).strip()
        if _es_ubicacion_demasiado_general(ubicacion_limpia):
            continue
        if ubicacion_limpia and ubicacion_limpia not in limpias:
            limpias.append(ubicacion_limpia)
    return limpias


def _es_ubicacion_demasiado_general(ubicacion: str) -> bool:
    return _normalizar_texto(ubicacion) in {"", "medellin", "medellin colombia"}


def _parsear_google_rss(xml_text: str, ubicacion: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    noticias = []
    for item in root.findall(".//item"):
        titulo = html.unescape(item.findtext("title") or "")
        descripcion = html.unescape(item.findtext("description") or "")
        fuente = item.findtext("source") or "Google News RSS"
        resumen = _limpiar_html(descripcion) or titulo

        if titulo:
            noticias.append(
                {
                    "ubicacion": ubicacion,
                    "fuente": fuente,
                    "texto": titulo,
                    "resumen": resumen,
                }
            )

    return noticias


def _filtrar_por_ubicacion(
    noticias: list[dict[str, Any]],
    ubicacion: str,
) -> list[dict[str, Any]]:
    ubicacion_normalizada = _normalizar_texto(ubicacion)
    filtradas = []
    for noticia in noticias:
        texto = _normalizar_texto(
            f"{noticia.get('texto', '')} {noticia.get('resumen', '')}"
        )
        if ubicacion_normalizada in texto:
            filtradas.append(noticia)
    return filtradas


def _deduplicar(noticias: list[dict[str, Any]]) -> list[dict[str, Any]]:
    resultado = []
    vistos = set()
    for noticia in noticias:
        clave = (
            noticia.get("ubicacion"),
            (noticia.get("texto") or noticia.get("resumen") or "").lower(),
        )
        if not clave[1] or clave in vistos:
            continue
        vistos.add(clave)
        resultado.append(noticia)
    return resultado


def _limitar_resultados(noticias: list[dict[str, Any]]) -> list[dict[str, Any]]:
    por_ubicacion: dict[str, list[dict[str, Any]]] = {}
    for noticia in noticias:
        por_ubicacion.setdefault(str(noticia.get("ubicacion") or ""), []).append(noticia)

    resultado = []
    while len(resultado) < settings.news_max_resultados:
        agregado = False
        for grupo in por_ubicacion.values():
            if grupo and len(resultado) < settings.news_max_resultados:
                resultado.append(grupo.pop(0))
                agregado = True
        if not agregado:
            break
    return resultado


def _limpiar_html(texto: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", texto).strip()


def _calcular_impacto_score(noticia: Mapping[str, Any]) -> float:
    texto = _normalizar_texto(
        f"{noticia.get('texto', '')} {noticia.get('resumen', '')}"
    )
    positivas = [
        "comercio",
        "servicios",
        "conectividad",
        "valorizacion",
        "educativa",
        "seguridad",
        "reduccion de delitos",
        "reduccion de homicidios",
        "oferta",
        "transporte",
        "crecimiento",
        "renovacion",
        "demanda",
    ]
    negativas = [
        "precios altos",
        "precio alto",
        "inseguridad",
        "hurto",
        "robo",
        "robos",
        "roban",
        "atraco",
        "extorsion",
        "bandas",
        "criminales",
        "balacera",
        "disparo",
        "tiroteo",
        "ladron",
        "asesinado",
        "muerto",
        "muerte",
        "homicidio",
        "delitos",
        "cierre total",
        "emergencia",
        "congestion",
        "saturacion",
        "incertidumbre",
        "variabilidad",
        "deterioro",
        "ruido",
    ]
    puntos = sum(1 for palabra in positivas if palabra in texto)
    puntos -= sum(1 for palabra in negativas if palabra in texto)

    if puntos > 0:
        return min(0.1, puntos * 0.025)
    if puntos < 0:
        return max(-0.1, puntos * 0.025)
    return 0.0


def _normalizar_texto(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor).lower())
    return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))


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
    noticia = _normalizar_texto(ubicacion_noticia)
    equivalencias = {
        "sur": {"envigado", "sabaneta"},
        "norte": {"robledo"},
        "occidente": {"laureles", "belen", "robledo"},
        "poblado": {"el poblado"},
    }

    if noticia in ubicaciones:
        return True

    return any(noticia in equivalencias.get(ubicacion, set()) for ubicacion in ubicaciones)
