"""
state/models.py — Versión corregida para Persona 2 (Adquisición de datos).
Alineada con el diagrama de flujo (nodos A-G).

Cambios respecto a la versión provisional:
  - zonas_candidatas   : nuevo campo, out de nodo B (antes solo existía zonas_relevantes)
  - propiedades_rankeadas: nuevo campo, out de nodo C (lo que entra al rombo ¿len ≥ min?)
  - decision_final     : renombrado/separado de resultado_final, out de nodo G
  - Campos de Persona 2 marcados con # P2
  - Campos de Persona 1 marcados con # P1
"""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── Sub-modelos ─────────────────────────────────────────────────────────────

class CriteriosUsuario(BaseModel):
    ciudad: str = "Medellín"
    tipo_inmueble: str = "apartamento"       # apartamento | casa | ...
    precio_min: Optional[int] = None         # COP
    precio_max: Optional[int] = None         # COP
    area_min: Optional[float] = None         # m²
    area_max: Optional[float] = None         # m²
    habitaciones_min: Optional[int] = None
    barrios_preferidos: list[str] = Field(default_factory=list)
    palabras_clave: list[str] = Field(default_factory=list)
    modalidad: str = "venta"                 # venta | arriendo


class Propiedad(BaseModel):
    id: str
    titulo: str
    precio: Optional[int] = None
    area: Optional[float] = None
    habitaciones: Optional[int] = None
    banos: Optional[int] = None
    barrio: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    url: str
    fuente: str                              # "fincaraiz" | "metrocuadrado"
    descripcion: Optional[str] = None
    imagenes: list[str] = Field(default_factory=list)
    score: Optional[float] = None           # asignado por nodo G (Persona 1)


class ZonaInfo(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    estrato_promedio: Optional[int] = None
    seguridad_score: Optional[float] = None
    acceso_transporte: Optional[str] = None
    notas_adicionales: Optional[str] = None


class IteracionLog(BaseModel):
    numero: int
    criterios_usados: dict[str, Any]
    total_resultados: int
    razon_reintento: Optional[str] = None


# ─── Estado principal ─────────────────────────────────────────────────────────

class EstadoSistema(BaseModel):

    # — Entrada del usuario (nodo A) —
    texto_libre_usuario: str = ""                                               # P1
    criterios_originales: CriteriosUsuario = Field(default_factory=CriteriosUsuario)  # P1: out de A

    # — Criterios en evolución —
    criterios_actuales: CriteriosUsuario = Field(default_factory=CriteriosUsuario)   # P2 lee, E modifica

    # — Zonas / contexto urbano (nodo B) —
    zonas_candidatas: list[ZonaInfo] = Field(default_factory=list)             # P2: out de B → entra a C
    zonas_relevantes: list[ZonaInfo] = Field(default_factory=list)             # P2: subconjunto final usado
    contexto_noticias: list[dict[str, str]] = Field(default_factory=list)      # P2: contexto auxiliar de B

    # — Propiedades (nodo C) —
    propiedades_raw: list[Propiedad] = Field(default_factory=list)             # P2: scraping crudo
    propiedades_rankeadas: list[Propiedad] = Field(default_factory=list)       # P2: out de C, entra al rombo
    propiedades_filtradas: list[Propiedad] = Field(default_factory=list)       # P1: post-rombo ¿len ≥ min?
    propuesta_actual: list[Propiedad] = Field(default_factory=list)            # P1: top-N para evaluación

    # — Control de flujo —
    iteracion_actual: int = 0                                                  # P1
    max_iteraciones: int = 5                                                   # P1
    nivel_relajacion: int = 0                                                  # P1: 0 = sin relajar
    historial_iteraciones: list[IteracionLog] = Field(default_factory=list)    # P1

    # — Diagnóstico (nodo D) —
    diagnostico_fallo: Optional[str] = None                                    # P1: out de D

    # — Evaluación (nodo G) — Persona 1 produce esto —
    decision_final: Optional[dict[str, Any]] = None                            # P1: out de G (score + coherencia)
    evaluacion_aprobada: bool = False                                           # P1: out del rombo ¿aprueba?

    # — Resultado final (nodo F) —
    resultado_final: Optional[dict[str, Any]] = None                           # P1: out de F (explicacion)
    listo: bool = False                                                         # P1