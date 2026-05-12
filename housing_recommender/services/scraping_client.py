"""
services/scraping_client.py
Estrategia: interceptar las llamadas XHR que hace fincaraiz.com.co
en lugar de parsear HTML. Más estable ante cambios de UI.

Fallback: httpx directo si los endpoints internos están disponibles.
"""
from __future__ import annotations

import asyncio
import re
import unicodedata
from typing import Optional
from urllib.parse import urlencode
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from config.settings import settings
from state.models import CriteriosUsuario, Propiedad

# ─── Constantes ──────────────────────────────────────────────────────────────

FINCARAIZ_BASE = "https://www.fincaraiz.com.co"
FINCARAIZ_API  = "https://api.fincaraiz.com.co"          # endpoint interno
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-CO,es;q=0.9",
    "Referer": FINCARAIZ_BASE,
}

TIPO_MAP = {
    "apartamento": "apartamentos",
    "casa": "casas",
    "oficina": "oficinas",
    "local": "locales-comerciales",
    "lote": "lotes",
}

MODALIDAD_MAP = {
    "venta": "venta",
    "arriendo": "arriendo",
}

BARRIO_PATHS = {
    "poblado": "el-poblado/suroriente/medellin",
    "el poblado": "el-poblado/suroriente/medellin",
}


def _debug(mensaje: str) -> None:
    if settings.log_level.upper() == "DEBUG":
        print(f"[scraping_client] {mensaje}")


def _slug(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto)
    ascii_text = normalizado.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def _url_busqueda_publica(criterios: CriteriosUsuario, pagina: int = 1) -> str:
    tipo = TIPO_MAP.get(criterios.tipo_inmueble.lower(), "apartamentos")
    modalidad = MODALIDAD_MAP.get(criterios.modalidad.lower(), "venta")
    ciudad_slug = _slug(criterios.ciudad)

    barrio = criterios.barrios_preferidos[0].lower() if criterios.barrios_preferidos else ""
    barrio_path = BARRIO_PATHS.get(barrio)

    if barrio_path:
        path = f"/{modalidad}/{tipo}/{barrio_path}"
    else:
        path = f"/{modalidad}/{tipo}/{ciudad_slug}/antioquia"

    url = f"{FINCARAIZ_BASE}{path}"
    if pagina > 1:
        url = f"{url}?pagina={pagina}"
    return url


# ─── Parser de resultados ─────────────────────────────────────────────────────

def _parsear_listing(raw: dict, fuente: str = "fincaraiz") -> Optional[Propiedad]:
    """Convierte un dict crudo del JSON de Finca Raíz en un objeto Propiedad."""
    try:
        precio_raw = raw.get("precio") or raw.get("price") or 0
        precio = int(re.sub(r"[^\d]", "", str(precio_raw))) if precio_raw else None

        return Propiedad(
            id=str(raw.get("id") or raw.get("_id") or ""),
            titulo=raw.get("titulo") or raw.get("title") or "Sin título",
            precio=precio,
            area=float(raw.get("area") or raw.get("areaTotal") or 0) or None,
            habitaciones=raw.get("habitaciones") or raw.get("bedrooms"),
            banos=raw.get("banos") or raw.get("bathrooms"),
            barrio=raw.get("barrio") or raw.get("neighborhood"),
            direccion=raw.get("direccion") or raw.get("address"),
            ciudad=raw.get("ciudad") or raw.get("city"),
            url=raw.get("url") or raw.get("link") or "",
            fuente=raw.get("fuente") or fuente,
            descripcion=raw.get("descripcion") or raw.get("description"),
            imagenes=raw.get("imagenes") or raw.get("images") or [],
        )
    except Exception:
        return None


def _parsear_card_html(texto: str, url: str, idx: int) -> Optional[dict]:
    precio_match = re.search(r"\$[\s\d.,]+", texto)
    area_match = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", texto, re.IGNORECASE)
    hab_match = re.search(r"(\d+)\s*Hab", texto, re.IGNORECASE)
    banos_match = re.search(r"(\d+)\s*Baño", texto, re.IGNORECASE)
    titulo_match = re.search(r"((?:Apartamento|Casa|Apartaestudio|Oficina|Local|Lote)[^.]*)", texto, re.IGNORECASE)

    if not precio_match and not area_match and not titulo_match:
        return None

    precio = int(re.sub(r"[^\d]", "", precio_match.group(0))) if precio_match else None
    area = float(area_match.group(1).replace(",", ".")) if area_match else None
    titulo = titulo_match.group(1).strip() if titulo_match else texto[:120]

    return {
        "id": url or f"html-{idx}",
        "titulo": titulo[:180],
        "precio": precio,
        "area": area,
        "habitaciones": int(hab_match.group(1)) if hab_match else None,
        "banos": int(banos_match.group(1)) if banos_match else None,
        "barrio": _extraer_barrio_desde_texto(texto),
        "ciudad": "Medellín" if "medellín" in texto.lower() else None,
        "url": url,
        "fuente": "fincaraiz-html",
        "descripcion": texto[:500],
    }


def _extraer_barrio_desde_texto(texto: str) -> Optional[str]:
    match = re.search(r"en ([a-záéíóúñ\s]+),\s*medell[ií]n", texto, re.IGNORECASE)
    if match:
        return match.group(1).strip().title()
    return None


def _filtrar_raw_items(raw_items: list[dict], criterios: CriteriosUsuario) -> list[dict]:
    filtrados: list[dict] = []
    barrios = [b.lower() for b in criterios.barrios_preferidos]

    for item in raw_items:
        texto = " ".join(str(v) for v in item.values() if v).lower()
        precio = item.get("precio")

        if criterios.precio_min and precio and precio < criterios.precio_min:
            continue
        if criterios.precio_max and precio and precio > criterios.precio_max:
            continue
        if criterios.area_min and item.get("area") and item["area"] < criterios.area_min:
            continue
        if criterios.habitaciones_min and item.get("habitaciones") and item["habitaciones"] < criterios.habitaciones_min:
            continue
        if barrios and not any(barrio in texto for barrio in barrios):
            continue

        filtrados.append(item)

    return filtrados


# ─── Cliente httpx (endpoint interno) ────────────────────────────────────────

async def _buscar_httpx(criterios: CriteriosUsuario, pagina: int = 1) -> list[dict]:
    """
    Intenta golpear el endpoint interno de búsqueda de Finca Raíz.
    Finca Raíz expone algo similar a:
      GET /listings/search?ciudad=medellin&tipo=apartamentos&modalidad=venta&page=1
    Los nombres exactos pueden variar; este wrapper normaliza los parámetros.
    """
    tipo = TIPO_MAP.get(criterios.tipo_inmueble.lower(), "apartamentos")
    modalidad = MODALIDAD_MAP.get(criterios.modalidad.lower(), "venta")

    params: dict = {
        "ciudad": criterios.ciudad.lower().replace(" ", "-"),
        "tipo": tipo,
        "modalidad": modalidad,
        "pagina": pagina,
        "cantidad": 20,
    }
    if criterios.precio_min:
        params["precioDesde"] = criterios.precio_min
    if criterios.precio_max:
        params["precioHasta"] = criterios.precio_max
    if criterios.area_min:
        params["areaDesde"] = criterios.area_min
    if criterios.habitaciones_min:
        params["habitaciones"] = criterios.habitaciones_min
    if criterios.barrios_preferidos:
        params["barrio"] = ",".join(criterios.barrios_preferidos)

    url = f"{FINCARAIZ_API}/listings/search?{urlencode(params)}"

    _debug(f"httpx GET {url}")

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
        _debug(f"httpx status={resp.status_code} content-type={resp.headers.get('content-type')}")
        resp.raise_for_status()
        data = resp.json()

    # Finca Raíz puede devolver {results: [...]} o directamente [...]
    if isinstance(data, list):
        return data
    return data.get("results") or data.get("listings") or data.get("data") or []


async def _buscar_html_httpx(criterios: CriteriosUsuario, pagina: int = 1) -> list[dict]:
    url = _url_busqueda_publica(criterios, pagina)
    _debug(f"html GET {url}")

    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        resp = await client.get(url)
        _debug(f"html status={resp.status_code} content-type={resp.headers.get('content-type')}")
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    raw_items: list[dict] = []

    for idx, anchor in enumerate(soup.find_all("a")):
        texto = " ".join(anchor.get_text(" ", strip=True).split())
        if "$" not in texto or "m²" not in texto:
            continue
        href = anchor.get("href") or ""
        item = _parsear_card_html(texto, urljoin(FINCARAIZ_BASE, href), idx)
        if item:
            raw_items.append(item)

    raw_items = _filtrar_raw_items(raw_items, criterios)
    _debug(f"html parseo {len(raw_items)} items crudos filtrados")
    return raw_items


# ─── Cliente Playwright (scraping de red) ────────────────────────────────────

async def _buscar_playwright(criterios: CriteriosUsuario, pagina: int = 1) -> list[dict]:
    """
    Abre Finca Raíz en un navegador headless e intercepta las peticiones XHR
    que carga la página de resultados. Más robusto que parsear HTML.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("Playwright no instalado. Ejecuta: pip install playwright && playwright install chromium")

    tipo = TIPO_MAP.get(criterios.tipo_inmueble.lower(), "apartamentos")
    modalidad = MODALIDAD_MAP.get(criterios.modalidad.lower(), "venta")
    url_busqueda = _url_busqueda_publica(criterios, pagina)
    _debug(f"playwright goto {url_busqueda}")

    captured: list[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="es-CO",
        )
        page = await context.new_page()

        # Interceptar respuestas JSON de la API interna
        async def on_response(response):
            if "listings" in response.url or "search" in response.url:
                try:
                    body = await response.json()
                    items = (
                        body if isinstance(body, list)
                        else body.get("results") or body.get("listings") or []
                    )
                    captured.extend(items)
                except Exception:
                    pass

        page.on("response", on_response)

        await page.goto(url_busqueda, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(2)  # dar tiempo a XHR tardíos

        await browser.close()

    _debug(f"playwright capturo {len(captured)} items crudos")
    return captured


# ─── Interfaz pública ─────────────────────────────────────────────────────────

async def buscar_propiedades(
    criterios: CriteriosUsuario,
    paginas: int = 2,
) -> list[Propiedad]:
    """
    Punto de entrada principal. Intenta httpx primero; si falla usa Playwright.
    Devuelve lista de Propiedad lista para guardar en estado.
    """
    raw_items: list[dict] = []

    for pagina in range(1, paginas + 1):
        try:
            items = await _buscar_html_httpx(criterios, pagina)
            _debug(f"pagina {pagina}: HTML devolvio {len(items)} items crudos")
            raw_items.extend(items)
        except Exception as exc:
            try:
                _debug(f"pagina {pagina}: HTML fallo ({type(exc).__name__}: {exc}); intentando API interna")
                items = await _buscar_httpx(criterios, pagina)
                _debug(f"pagina {pagina}: API devolvio {len(items)} items crudos")
                raw_items.extend(items)
            except Exception as api_exc:
                _debug(f"pagina {pagina}: API fallo ({type(api_exc).__name__}: {api_exc}); intentando Playwright")
                try:
                    items = await _buscar_playwright(criterios, pagina)
                    _debug(f"pagina {pagina}: Playwright devolvio {len(items)} items crudos")
                    raw_items.extend(items)
                except Exception as e:
                    print(f"[scraping_client] Error en página {pagina}: {e}")

    raw_items = _deduplicar_raw_items(raw_items)
    propiedades = [_parsear_listing(r) for r in raw_items]
    propiedades_validas = [p for p in propiedades if p is not None]
    _debug(f"total crudo={len(raw_items)} parseadas={len(propiedades_validas)}")
    return propiedades_validas


def _deduplicar_raw_items(raw_items: list[dict]) -> list[dict]:
    vistos: set[str] = set()
    unicos: list[dict] = []
    for item in raw_items:
        key = str(item.get("url") or item.get("id") or item)
        if key in vistos:
            continue
        vistos.add(key)
        unicos.append(item)
    return unicos


# ─── Mock para tests ──────────────────────────────────────────────────────────

def mock_propiedades(criterios: CriteriosUsuario, n: int = 5) -> list[Propiedad]:
    """Genera propiedades falsas para tests sin red."""
    return [
        Propiedad(
            id=f"mock-{i}",
            titulo=f"Apartamento {i+1} en {criterios.ciudad}",
            precio=(criterios.precio_max or 500_000_000) - i * 10_000_000,
            area=(criterios.area_min or 60) + i * 5,
            habitaciones=(criterios.habitaciones_min or 2) + (i % 2),
            banos=2,
            barrio=criterios.barrios_preferidos[0] if criterios.barrios_preferidos else "El Poblado",
            ciudad=criterios.ciudad,
            url=f"https://www.fincaraiz.com.co/inmueble/mock-{i}",
            fuente="mock",
        )
        for i in range(n)
    ]
