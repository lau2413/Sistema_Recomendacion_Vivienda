# state/models.py
from typing import Any, Optional, Literal, Annotated
from pydantic import BaseModel, Field
from operator import add


# ============================================================
# SUB-MODELOS DE DOMINIO
# ============================================================

class Requisito(BaseModel):
    """Lo que el usuario pide. Mismos campos que Propiedad, sin score."""
    ubicacion: Optional[str] = None
    precio_max: Optional[float] = None
    habitaciones: Optional[int] = None
    banos: Optional[int] = None
    parqueadero: Optional[int] = None
    tipo: Optional[Literal["apartamento", "casa", "apartaestudio"]] = None
    area_min: Optional[float] = None
    administracion_max: Optional[float] = None


class Propiedad(BaseModel):
    """Una vivienda encontrada por el scraper."""
    ubicacion: str
    precio: float
    habitaciones: int
    banos: int
    parqueadero: int
    tipo: str
    area: float
    administracion: Optional[float] = None
    score: Optional[float] = Field(
        default=None,
        description="Qué tanto cumple esta propiedad los requisitos. La asigna el evaluador."
    )


class Noticia(BaseModel):
    """Pieza de contexto del sector inmobiliario."""
    fuente: str
    texto: str
    resumen: str


class Propuesta(BaseModel):
    """Conjunto de propiedades recomendadas con un score general."""
    propiedades: list[Propiedad]
    score: Optional[float] = Field(
        default=None,
        description="Score global de la propuesta. Determina si se acepta o se relajan requisitos."
    )


class Evaluacion(BaseModel):
    """Resultado del nodo evaluador sobre la propuesta actual."""
    es_aceptable: bool
    score: float = Field(description="Score entre 0 y 10.")
    razon: str = Field(description="Explicación de por qué se acepta o se rechaza.")
    recomendacion: Optional[str] = Field(
        default=None,
        description="Qué criterio relajar si no es aceptable (e.g. 'precio', 'area', 'habitaciones')."
    )


class EntradaRelajacion(BaseModel):
    """Registro de una ronda de relajación de criterios."""
    iteracion: int
    campo_relajado: str = Field(description="Nombre del campo modificado (e.g. 'precio_max').")
    valor_antes: Any = Field(description="Valor del campo antes de relajar.")
    valor_despues: Any = Field(description="Valor del campo después de relajar.")
    descripcion: str = Field(description="Texto legible del cambio realizado.")


# ============================================================
# ESTADO PRINCIPAL DEL GRAFO
# ============================================================

class AgentState(BaseModel):
    """Estado que viaja por todo el grafo de LangGraph."""

    # Entrada del usuario (lo único que existe al iniciar)
    textoUsuario: str

    # Criterios: originales (inmutables) y actuales (evolucionan con relajación)
    requisitos_originales: Optional[Requisito] = None
    requisitos: Optional[Requisito] = None

    # Zonas identificadas y seleccionadas para la búsqueda
    zonas_analizadas: list[str] = Field(default_factory=list)
    zonas_seleccionadas: list[str] = Field(default_factory=list)

    # Resultados de búsqueda y filtrado
    propiedades: Optional[list[Propiedad]] = None
    propiedades_filtradas: Optional[list[Propiedad]] = None

    # Contexto externo (noticias/señales del sector)
    noticias: Optional[list[Noticia]] = None
    diagnostico_noticias: Optional[Any] = None

    # Propuesta construida y evaluación de calidad
    propuesta: Optional[Propuesta] = None
    evaluacion: Optional[Evaluacion] = None

    # Trazabilidad de la relajación
    historial_relajacion: list[EntradaRelajacion] = Field(default_factory=list)
    diagnostico: Optional[str] = None
    mensaje_relajacion: Optional[str] = None
    relajacion_completa: bool = False
    nivel_relajacion_aplicado: float = 0.0

    # Resultados finales formateados para el usuario
    recomendaciones_finales: list[str] = Field(default_factory=list)
    explicaciones: list[str] = Field(default_factory=list)

    # Control del ciclo de relajación
    iteracion: int = 0
    max_iteraciones: int = 3
