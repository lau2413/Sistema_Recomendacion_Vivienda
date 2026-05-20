"""Presentacion final de la recomendacion de vivienda."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def presentar_resultado(estado: Any) -> dict[str, Any]:
    """Nodo del grafo: prepara recomendaciones_finales y explicaciones."""

    recomendaciones, explicaciones = generar_recomendaciones(estado)
    return {
        "recomendaciones_finales": recomendaciones,
        "explicaciones": explicaciones,
    }


def generar_recomendaciones(estado: Any) -> tuple[list[str], list[str]]:
    """Genera texto final desde propuesta, requisitos, historial, noticias y evaluacion."""

    propuesta = _a_dict(_get(estado, "propuesta", {}) or {})
    requisitos = _a_dict(_get(estado, "requisitos", {}) or {})
    requisitos_originales = _a_dict(_get(estado, "requisitos_originales", {}) or {})
    historial = [_a_dict(item) for item in (_get(estado, "historial_relajacion", []) or [])]
    noticias = [_a_dict(item) for item in (_get(estado, "noticias", []) or [])]
    evaluacion = _a_dict(_get(estado, "evaluacion", {}) or {})
    diagnostico = _get(estado, "diagnostico")
    diagnostico_noticias = _get(estado, "diagnostico_noticias")

    propiedades = [_a_dict(prop) for prop in (propuesta.get("propiedades") or [])]
    recomendaciones = [
        _formatear_propiedad(indice, propiedad, requisitos)
        for indice, propiedad in enumerate(propiedades, start=1)
    ]

    explicaciones = [
        _resumen_requisitos("Requisitos originales", requisitos_originales),
        _resumen_requisitos("Requisitos usados", requisitos),
        _resumen_evaluacion(evaluacion),
        _resumen_historial(historial),
        _resumen_noticias(noticias),
    ]

    if diagnostico:
        explicaciones.append(f"Diagnostico: {diagnostico}")
    if diagnostico_noticias:
        explicaciones.append(f"Diagnostico noticias: {diagnostico_noticias}")

    if not recomendaciones:
        recomendaciones = [
            "No se pudo construir una propuesta con los requisitos actuales."
        ]

    return recomendaciones, [texto for texto in explicaciones if texto]


def presentar_resultados(estado: Any) -> None:
    """Funcion de compatibilidad para imprimir resultados en consola."""

    recomendaciones, explicaciones = generar_recomendaciones(estado)

    print("\n" + "=" * 80)
    print("RESULTADOS DE LA BUSQUEDA DE VIVIENDA")
    print("=" * 80 + "\n")

    print("RESUMEN:")
    for explicacion in explicaciones:
        print(f"- {explicacion}")

    print("\nRECOMENDACIONES:")
    for recomendacion in recomendaciones:
        print(f"- {recomendacion}")

    print("\n" + "=" * 80)


def _formatear_propiedad(
    indice: int,
    propiedad: Mapping[str, Any],
    requisitos: Mapping[str, Any],
) -> str:
    partes = [
        f"{indice}. {propiedad.get('tipo', 'Vivienda')} en {propiedad.get('ubicacion', 'ubicacion no disponible')}",
        f"precio ${float(propiedad.get('precio') or 0):,.0f}",
        f"{float(propiedad.get('area') or 0):.0f} m2",
        f"{int(propiedad.get('habitaciones') or 0)} hab.",
        f"{int(propiedad.get('banos') or 0)} banos",
    ]
    if propiedad.get("parqueadero") is not None:
        partes.append(f"{int(propiedad.get('parqueadero') or 0)} parqueaderos")
    if propiedad.get("score") is not None:
        partes.append(f"score {float(propiedad['score']):.2f}")

    cumplimiento = _cumplimiento_resumido(propiedad, requisitos)
    if cumplimiento:
        partes.append(cumplimiento)

    return " | ".join(partes)


def _cumplimiento_resumido(
    propiedad: Mapping[str, Any],
    requisitos: Mapping[str, Any],
) -> str:
    cumplidos = []
    if requisitos.get("precio_max") is not None and propiedad.get("precio") is not None:
        cumplidos.append("precio" if propiedad["precio"] <= requisitos["precio_max"] else "precio ajustado")
    if requisitos.get("area_min") is not None and propiedad.get("area") is not None:
        cumplidos.append("area" if propiedad["area"] >= requisitos["area_min"] else "area ajustada")
    if requisitos.get("habitaciones") is not None and propiedad.get("habitaciones") is not None:
        cumplidos.append(
            "habitaciones"
            if propiedad["habitaciones"] >= requisitos["habitaciones"]
            else "habitaciones ajustadas"
        )
    if not cumplidos:
        return ""
    return "cumple: " + ", ".join(cumplidos)


def _resumen_requisitos(titulo: str, requisitos: Mapping[str, Any]) -> str:
    if not requisitos:
        return f"{titulo}: no disponibles."
    campos = ", ".join(
        f"{campo}={valor}" for campo, valor in requisitos.items() if valor is not None
    )
    return f"{titulo}: {campos}."


def _resumen_evaluacion(evaluacion: Mapping[str, Any]) -> str:
    if not evaluacion:
        return "Evaluacion: no disponible."
    estado = "aceptada" if evaluacion.get("es_aceptable") else "requiere ajustes"
    score = evaluacion.get("score")
    razon = evaluacion.get("razon") or "sin razon registrada"
    if score is None:
        return f"Evaluacion {estado}: {razon}."
    return f"Evaluacion {estado} con score {float(score):.2f}/10: {razon}"


def _resumen_historial(historial: list[Mapping[str, Any]]) -> str:
    if not historial:
        return "Relajacion: no se modificaron los requisitos."
    cambios = [
        f"{item.get('campo_relajado')} ({item.get('valor_antes')} -> {item.get('valor_despues')})"
        for item in historial
    ]
    return "Relajacion aplicada: " + "; ".join(cambios) + "."


def _resumen_noticias(noticias: list[Mapping[str, Any]]) -> str:
    if not noticias:
        return "Noticias/contexto: no se encontraron senales externas relevantes."
    resumenes = [
        str(noticia.get("resumen") or noticia.get("texto") or "").strip()
        for noticia in noticias[:3]
    ]
    resumenes = [resumen for resumen in resumenes if resumen]
    if not resumenes:
        return "Noticias/contexto: disponibles sin resumen."
    return "Noticias/contexto: " + " | ".join(resumenes)


def _get(valor: Any, campo: str, default: Any = None) -> Any:
    if isinstance(valor, Mapping):
        return valor.get(campo, default)
    return getattr(valor, campo, default)


def _a_dict(valor: Any) -> dict[str, Any]:
    if isinstance(valor, Mapping):
        return dict(valor)
    if hasattr(valor, "model_dump"):
        return valor.model_dump(exclude_none=True)
    if hasattr(valor, "dict"):
        return valor.dict(exclude_none=True)
    return {}
