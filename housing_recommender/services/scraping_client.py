from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Protocol
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from housing_recommender.config.settings import settings


class ScrapingClient(Protocol):
    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        ...


class FincaRaizScrapingClient:
    """Scraper Playwright para resultados publicos de Finca Raiz."""

    def __init__(
        self,
        max_resultados: int | None = None,
        timeout_ms: int | None = None,
        headless: bool = True,
    ) -> None:
        self.max_resultados = max_resultados or settings.finca_raiz_max_resultados
        self.timeout_ms = timeout_ms or settings.finca_raiz_timeout_ms
        self.headless = headless

    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        requisitos_normalizados = _normalizar_requisitos(requisitos)
        url = _construir_url_fincaraiz(requisitos_normalizados)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                page = browser.new_page(locale="es-CO", user_agent=_user_agent())
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                page.wait_for_timeout(2500)
                propiedades = self._extraer_propiedades(page)
                browser.close()
        except (PlaywrightError, PlaywrightTimeoutError):
            return []

        return [
            propiedad
            for propiedad in propiedades
            if _cumple_requisitos(propiedad, requisitos_normalizados)
        ][: self.max_resultados]

    def _extraer_propiedades(self, page: Any) -> list[dict[str, Any]]:
        cards = page.locator("a[href*='/inmueble/'], a[href*='/apartamento-'], a[href*='/casa-']")
        propiedades: list[dict[str, Any]] = []
        vistos: set[str] = set()

        for index in range(min(cards.count(), self.max_resultados * 4)):
            card = cards.nth(index)
            href = card.get_attribute("href") or ""
            texto = _limpiar_espacios(card.inner_text(timeout=3000))
            if not texto or len(texto) < 20:
                continue

            url = href if href.startswith("http") else f"https://www.fincaraiz.com.co{href}"
            if url in vistos:
                continue

            propiedad = _parsear_texto_propiedad(texto)
            if propiedad is None:
                continue

            propiedad["url"] = url
            propiedad["fuente"] = "fincaraiz"
            propiedades.append(propiedad)
            vistos.add(url)

            if len(propiedades) >= self.max_resultados:
                break

        if propiedades:
            return propiedades

        texto_pagina = _limpiar_espacios(page.locator("body").inner_text(timeout=5000))
        propiedades = [
            propiedad
            for propiedad in (_parsear_texto_propiedad(bloque) for bloque in _partir_bloques(texto_pagina))
            if propiedad is not None
        ]
        for propiedad in propiedades:
            propiedad["fuente"] = "fincaraiz"
        return propiedades[: self.max_resultados]


class MetrocuadradoScrapingClient:
    """Cliente HTTP para el JSON que Metrocuadrado inserta en el payload Next."""

    def __init__(self, max_resultados: int | None = None, timeout_s: float = 20) -> None:
        self.max_resultados = max_resultados or settings.finca_raiz_max_resultados
        self.timeout_s = timeout_s

    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        requisitos_normalizados = _normalizar_requisitos(requisitos)
        url = _construir_url_metrocuadrado(requisitos_normalizados)
        html_text = _descargar_html(url, self.timeout_s)
        if not html_text:
            return []

        propiedades = _parsear_metrocuadrado_html(html_text)
        return [
            propiedad
            for propiedad in propiedades
            if _cumple_requisitos(propiedad, requisitos_normalizados)
        ][: self.max_resultados]


class CiencuadrasScrapingClient:
    """Scraper HTTP para resultados publicos renderizados por Ciencuadras."""

    def __init__(self, max_resultados: int | None = None, timeout_s: float = 20) -> None:
        self.max_resultados = max_resultados or settings.finca_raiz_max_resultados
        self.timeout_s = timeout_s

    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        requisitos_normalizados = _normalizar_requisitos(requisitos)
        url = _construir_url_ciencuadras(requisitos_normalizados)
        html_text = _descargar_html(url, self.timeout_s)
        if not html_text:
            return []

        propiedades = _parsear_ciencuadras_html(html_text)
        return [
            propiedad
            for propiedad in propiedades
            if _cumple_requisitos(propiedad, requisitos_normalizados)
        ][: self.max_resultados]


class ScrapingMixtoClient:
    """Combina portales reales y elimina duplicados por URL."""

    def __init__(self, max_resultados: int | None = None) -> None:
        self.max_resultados = max_resultados or settings.finca_raiz_max_resultados
        self.proveedores: list[ScrapingClient] = [
            MetrocuadradoScrapingClient(max_resultados=self.max_resultados),
            CiencuadrasScrapingClient(max_resultados=self.max_resultados),
            FincaRaizScrapingClient(max_resultados=self.max_resultados),
        ]

    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        propiedades: list[dict[str, Any]] = []
        for proveedor in self.proveedores:
            propiedades.extend(proveedor.buscar(requisitos))
        return _deduplicar_propiedades(propiedades)[: self.max_resultados]


class MockScrapingClient:
    def buscar(self, requisitos: Mapping[str, Any]) -> list[dict[str, Any]]:
        requisitos_normalizados = _normalizar_requisitos(requisitos)
        return [
            propiedad
            for propiedad in _propiedades_demo()
            if _cumple_requisitos(propiedad, requisitos_normalizados)
        ]


def obtener_propiedades(
    requisitos: Mapping[str, Any],
    client: ScrapingClient | None = None,
) -> list[dict[str, Any]]:
    proveedor = client or _crear_cliente_por_configuracion()
    propiedades = proveedor.buscar(requisitos)

    if not propiedades and not isinstance(proveedor, MockScrapingClient):
        propiedades = MockScrapingClient().buscar(requisitos)

    return [_normalizar_propiedad(propiedad) for propiedad in propiedades]


def _crear_cliente_por_configuracion() -> ScrapingClient:
    if settings.scraping_provider == "fincaraiz":
        return FincaRaizScrapingClient()
    if settings.scraping_provider == "metrocuadrado":
        return MetrocuadradoScrapingClient()
    if settings.scraping_provider == "ciencuadras":
        return CiencuadrasScrapingClient()
    if settings.scraping_provider == "mixto":
        return ScrapingMixtoClient()
    return MockScrapingClient()


def _construir_url_fincaraiz(requisitos: Mapping[str, Any]) -> str:
    tipo = str(requisitos.get("tipo") or "apartamentos").lower()
    tipo_segmento = {
        "apartamento": "apartamentos",
        "apartaestudio": "apartaestudios",
        "casa": "casas",
    }.get(tipo, "apartamentos")
    ubicacion = _normalizar_slug(str(requisitos.get("ubicacion") or "medellin"))
    return f"https://www.fincaraiz.com.co/venta/{tipo_segmento}/{ubicacion}"


def _construir_url_metrocuadrado(requisitos: Mapping[str, Any]) -> str:
    tipo = str(requisitos.get("tipo") or "apartamento").lower()
    tipo_segmento = {
        "apartamento": "apartamentos",
        "apartaestudio": "apartaestudios",
        "casa": "casas",
    }.get(tipo, "apartamentos")
    ubicacion = _segmento_metrocuadrado(str(requisitos.get("ubicacion") or "medellin"))
    return f"https://www.metrocuadrado.com/{tipo_segmento}/venta/{ubicacion}/"


def _construir_url_ciencuadras(requisitos: Mapping[str, Any]) -> str:
    tipo = str(requisitos.get("tipo") or "apartamento").lower()
    tipo_segmento = {
        "apartamento": "apartamento",
        "apartaestudio": "apartaestudio",
        "casa": "casa",
    }.get(tipo, "apartamento")
    ubicacion = _normalizar_texto(requisitos.get("ubicacion") or "medellin")
    if ubicacion in {"", "medellin"}:
        return f"https://www.ciencuadras.com/venta/medellin/{tipo_segmento}"
    return f"https://www.ciencuadras.com/venta/medellin/{_normalizar_slug(ubicacion)}/{tipo_segmento}"


def _segmento_metrocuadrado(ubicacion: str) -> str:
    ubicacion_normalizada = _normalizar_texto(ubicacion)
    if ubicacion_normalizada in {"", "medellin"}:
        return "medellin"
    return f"medellin/{_normalizar_slug(ubicacion_normalizada)}"


def _descargar_html(url: str, timeout_s: float) -> str:
    try:
        response = httpx.get(
            url,
            timeout=timeout_s,
            follow_redirects=True,
            headers=_headers_publicos(),
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return ""
    return response.text


def _parsear_metrocuadrado_html(html_text: str) -> list[dict[str, Any]]:
    texto = html_text.replace('\\"', '"').replace("\\/", "/")
    propiedades = []
    for bloque in texto.split('"contactPhone"')[1:]:
        titulo = _extraer_json_string(bloque, "title")
        link = _extraer_json_string(bloque, "link")
        precio = _numero_opcional(_extraer_json_valor(bloque, "mvalorventa"))
        area = _numero_opcional(_extraer_json_valor(bloque, "marea"))
        if precio is None or area is None:
            continue

        titulo = _limpiar_espacios(titulo or "")
        link = link or _extraer_json_string(bloque, "murldetalle") or ""
        if not titulo or not link:
            continue

        barrio = (
            _extraer_json_string(bloque, "mnombrecomunbarrio")
            or _extraer_json_string(bloque, "mbarrio")
            or titulo
        )
        url = link if link.startswith("http") else f"https://www.metrocuadrado.com{link}"
        propiedades.append(
            {
                "ubicacion": _normalizar_nombre_zona(barrio),
                "precio": precio,
                "habitaciones": int(_extraer_json_string(bloque, "mnrocuartos") or 0),
                "banos": int(_extraer_json_string(bloque, "mnrobanos") or 0),
                "parqueadero": int(_extraer_json_string(bloque, "mnrogarajes") or 0),
                "tipo": _extraer_tipo(titulo),
                "area": area,
                "administracion": None,
                "fuente": "metrocuadrado",
                "url": url,
            }
        )
    return _deduplicar_propiedades(propiedades)


def _parsear_ciencuadras_html(html_text: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html_text, "html.parser")
    propiedades: list[dict[str, Any]] = []
    vistos: set[str] = set()

    for enlace in soup.find_all("a", href=True):
        texto = _limpiar_espacios(enlace.get_text(" "))
        if "Valor de compra" not in texto or " m2 " not in f" {texto} ":
            continue

        propiedad = _parsear_texto_propiedad(texto)
        if propiedad is None:
            continue

        href = enlace["href"]
        url = href if href.startswith("http") else f"https://www.ciencuadras.com{href}"
        if url in vistos:
            continue
        propiedad["fuente"] = "ciencuadras"
        propiedad["url"] = url
        propiedades.append(propiedad)
        vistos.add(url)

    return propiedades


def _parsear_texto_propiedad(texto: str) -> dict[str, Any] | None:
    precio = _extraer_precio(texto)
    area = _extraer_numero_antes_de(texto, ["m2", "m²"])
    habitaciones = _extraer_numero_detalle(texto, ["hab", "habit", "habitacion", "habitaciones"])
    banos = _extraer_numero_detalle(texto, ["bano", "banos", "baño", "baños"])
    parqueadero = _extraer_numero_detalle(texto, ["garaje", "garajes", "parqueadero", "parqueaderos"])

    if precio is None or area is None:
        return None

    return {
        "ubicacion": _extraer_ubicacion_desde_texto(texto),
        "precio": precio,
        "habitaciones": habitaciones or 0,
        "banos": banos or 0,
        "parqueadero": parqueadero or 0,
        "tipo": _extraer_tipo(texto),
        "area": area,
        "administracion": _extraer_administracion(texto),
    }


def _cumple_requisitos(propiedad: Mapping[str, Any], requisitos: Mapping[str, Any]) -> bool:
    if requisitos.get("ubicacion") and not _ubicacion_coincide(propiedad["ubicacion"], requisitos["ubicacion"]):
        return False
    if requisitos.get("precio_max") is not None and propiedad["precio"] > requisitos["precio_max"]:
        return False
    if requisitos.get("habitaciones") is not None and propiedad["habitaciones"] < requisitos["habitaciones"]:
        return False
    if requisitos.get("banos") is not None and propiedad["banos"] < requisitos["banos"]:
        return False
    if requisitos.get("parqueadero") is not None and propiedad["parqueadero"] < requisitos["parqueadero"]:
        return False
    if requisitos.get("tipo") and propiedad["tipo"] != requisitos["tipo"]:
        return False
    if requisitos.get("area_min") is not None and propiedad["area"] < requisitos["area_min"]:
        return False
    if (
        requisitos.get("administracion_max") is not None
        and propiedad.get("administracion") is not None
        and propiedad["administracion"] > requisitos["administracion_max"]
    ):
        return False
    return True


def _normalizar_requisitos(requisitos: Mapping[str, Any]) -> dict[str, Any]:
    normalizados = dict(requisitos)

    for alias in ("baños", "banos"):
        if alias in normalizados and "banos" not in normalizados:
            normalizados["banos"] = normalizados.pop(alias)

    if normalizados.get("parqueadero") is not None:
        normalizados["parqueadero"] = int(normalizados["parqueadero"])

    return {clave: valor for clave, valor in normalizados.items() if valor is not None}


def _normalizar_propiedad(propiedad: Mapping[str, Any]) -> dict[str, Any]:
    normalizada = dict(propiedad)
    normalizada["habitaciones"] = int(normalizada.get("habitaciones") or 0)
    normalizada["banos"] = int(normalizada.get("banos") or 0)
    normalizada["parqueadero"] = int(normalizada.get("parqueadero") or 0)
    normalizada["precio"] = float(normalizada.get("precio") or 0)
    normalizada["area"] = float(normalizada.get("area") or 0)
    return normalizada


def _ubicacion_coincide(ubicacion_propiedad: Any, ubicacion_requisito: Any) -> bool:
    propiedad = _normalizar_texto(ubicacion_propiedad)
    requisito = _normalizar_texto(ubicacion_requisito)
    equivalencias = {
        "sur": {"envigado", "sabaneta"},
        "norte": {"robledo"},
        "occidente": {"laureles", "belen", "robledo"},
        "centro": {"centro", "la candelaria"},
        "poblado": {"el poblado", "poblado"},
        "el poblado": {"el poblado", "poblado"},
        "laureles": {"laureles", "laureles estadio"},
        "belen": {"belen"},
    }

    if requisito in propiedad or propiedad in requisito:
        return True

    return propiedad in equivalencias.get(requisito, set())


def _extraer_precio(texto: str) -> float | None:
    match = re.search(r"\$\s*([\d.,]+)", texto)
    if not match:
        return None
    return _numero_colombiano(match.group(1))


def _extraer_administracion(texto: str) -> float | None:
    match = re.search(r"administraci[oó]n\s*\$?\s*([\d.,]+)", texto, re.IGNORECASE)
    if not match:
        return None
    return _numero_colombiano(match.group(1))


def _extraer_numero_antes_de(texto: str, palabras: list[str]) -> int | None:
    patron = "|".join(re.escape(palabra) for palabra in palabras)
    match = re.search(rf"(\d+(?:[.,]\d+)?)\s*(?:{patron})", texto, re.IGNORECASE)
    if not match:
        return None
    return int(float(match.group(1).replace(",", ".")))


def _extraer_numero_detalle(texto: str, palabras: list[str]) -> int | None:
    patron = "|".join(re.escape(palabra) for palabra in palabras)
    match = re.search(rf"(?:{patron})\.?\s*(\d+(?:[.,]\d+)?)", texto, re.IGNORECASE)
    if match:
        return int(float(match.group(1).replace(",", ".")))
    return _extraer_numero_antes_de(texto, palabras)


def _extraer_tipo(texto: str) -> str:
    texto_lower = _normalizar_texto(texto)
    if "apartaestudio" in texto_lower:
        return "apartaestudio"
    if "casa" in texto_lower:
        return "casa"
    return "apartamento"


def _extraer_ubicacion_desde_texto(texto: str) -> str:
    zona_ciencuadras = re.search(
        r"medell[ií]n,\s*([^,]+)",
        texto,
        re.IGNORECASE,
    )
    if zona_ciencuadras:
        return _normalizar_nombre_zona(zona_ciencuadras.group(1))

    barrios = [
        "El Poblado",
        "Poblado",
        "Laureles Estadio",
        "Laureles",
        "Envigado",
        "Sabaneta",
        "Belen",
        "Belén",
        "Centro",
        "La Candelaria",
        "Robledo",
        "Castilla",
        "Guayabal",
        "Medellin",
        "Medellín",
    ]
    texto_normalizado = _normalizar_texto(texto)
    for barrio in barrios:
        if _normalizar_texto(barrio) in texto_normalizado:
            if _normalizar_texto(barrio) == "poblado":
                return "El Poblado"
            if _normalizar_texto(barrio) == "belen":
                return "Belen"
            if _normalizar_texto(barrio) == "medellin":
                return "Medellin"
            return barrio
    return "Medellin"


def _normalizar_nombre_zona(valor: Any) -> str:
    texto = _limpiar_espacios(str(valor or ""))
    if not texto:
        return "Medellin"
    texto_normalizado = _normalizar_texto(texto)
    equivalencias = {
        "poblado": "El Poblado",
        "el poblado": "El Poblado",
        "belen": "Belen",
        "medellin": "Medellin",
    }
    if texto_normalizado in equivalencias:
        return equivalencias[texto_normalizado]
    return texto.title()


def _numero_colombiano(valor: str) -> float:
    limpio = valor.replace(".", "").replace(",", "")
    return float(limpio)


def _numero_opcional(valor: Any) -> float | None:
    if valor is None or str(valor).lower() == "null" or str(valor).strip() == "":
        return None
    return float(valor)


def _extraer_json_string(texto: str, campo: str) -> str | None:
    match = re.search(rf'"{re.escape(campo)}":"([^"]*)"', texto)
    return match.group(1) if match else None


def _extraer_json_valor(texto: str, campo: str) -> str | None:
    match = re.search(rf'"{re.escape(campo)}":([^,}}]+)', texto)
    return match.group(1).strip('"') if match else None


def _normalizar_slug(valor: str) -> str:
    limpio = _normalizar_texto(valor).strip()
    return quote(re.sub(r"\s+", "-", limpio))


def _normalizar_texto(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor).lower())
    return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))


def _limpiar_espacios(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def _partir_bloques(texto: str) -> list[str]:
    return re.split(r"(?=\$\s*[\d.,]+)", texto)


def _headers_publicos() -> dict[str, str]:
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CO,es;q=0.9,en;q=0.7",
        "User-Agent": _user_agent(),
    }


def _user_agent() -> str:
    return (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )


def _deduplicar_propiedades(propiedades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    resultado = []
    vistos = set()
    for propiedad in propiedades:
        clave = propiedad.get("url") or (
            propiedad.get("fuente"),
            propiedad.get("ubicacion"),
            propiedad.get("precio"),
            propiedad.get("area"),
        )
        if clave in vistos:
            continue
        vistos.add(clave)
        resultado.append(propiedad)
    return resultado


def _propiedades_demo() -> list[dict[str, Any]]:
    return [
        {
            "ubicacion": "El Poblado",
            "precio": 760000000,
            "habitaciones": 3,
            "banos": 2,
            "parqueadero": 2,
            "tipo": "apartamento",
            "area": 92,
            "administracion": 420000,
            "fuente": "mock",
        },
        {
            "ubicacion": "Laureles",
            "precio": 590000000,
            "habitaciones": 3,
            "banos": 2,
            "parqueadero": 1,
            "tipo": "apartamento",
            "area": 84,
            "administracion": 310000,
            "fuente": "mock",
        },
        {
            "ubicacion": "Envigado",
            "precio": 680000000,
            "habitaciones": 4,
            "banos": 3,
            "parqueadero": 2,
            "tipo": "casa",
            "area": 118,
            "administracion": None,
            "fuente": "mock",
        },
        {
            "ubicacion": "Belen",
            "precio": 410000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": 0,
            "tipo": "apartamento",
            "area": 68,
            "administracion": 180000,
            "fuente": "mock",
        },
        {
            "ubicacion": "Sabaneta",
            "precio": 360000000,
            "habitaciones": 2,
            "banos": 2,
            "parqueadero": 1,
            "tipo": "apartamento",
            "area": 63,
            "administracion": 220000,
            "fuente": "mock",
        },
        {
            "ubicacion": "Centro",
            "precio": 285000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": 0,
            "tipo": "apartamento",
            "area": 58,
            "administracion": 120000,
            "fuente": "mock",
        },
        {
            "ubicacion": "El Poblado",
            "precio": 980000000,
            "habitaciones": 4,
            "banos": 3,
            "parqueadero": 2,
            "tipo": "casa",
            "area": 135,
            "administracion": None,
            "fuente": "mock",
        },
        {
            "ubicacion": "Robledo",
            "precio": 320000000,
            "habitaciones": 2,
            "banos": 1,
            "parqueadero": 0,
            "tipo": "apartamento",
            "area": 64,
            "administracion": 95000,
            "fuente": "mock",
        },
    ]
