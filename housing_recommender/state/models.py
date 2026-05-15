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
    fuente: Optional[str] = None
    url: Optional[str] = None
    score: Optional[float] = Field(
        default=None,
        description="Qué tanto cumple esta propiedad los requisitos. La asigna el evaluador."
    )


class Noticia(BaseModel):
    """Pieza de contexto del sector inmobiliario."""
    fuente: str
    texto: str
    resumen: str
    ubicacion: Optional[str] = None
    impacto_score: Optional[float] = Field(
        default=None,
        description="Ajuste sugerido al score de propiedades en esta zona."
    )


class Propuesta(BaseModel):
    """Conjunto de propiedades recomendadas con un score general."""
    propiedades: list[Propiedad]
    score: Optional[float] = Field(
        default=None,
        description="Score global de la propuesta. Determina si se acepta o se relajan requisitos."
    )


# ============================================================
# ESTADO PRINCIPAL DEL GRAFO
# ============================================================

class AgentState(BaseModel):
    """Estado que viaja por todo el grafo de LangGraph."""

    # Entrada del usuario (lo único que existe al iniciar)
    textoUsuario: str

    # Se van llenando nodo por nodo
    requisitos: Optional[Requisito] = None
    propiedades: Optional[list[Propiedad]] = None
    noticias: Optional[list[Noticia]] = None
    diagnostico_noticias: Optional[dict[str, Any]] = None
    propuesta: Optional[Propuesta] = None

    # Control del ciclo de relajación (mínimo necesario)
    iteracion: int = 0
    max_iteraciones: int = 3
