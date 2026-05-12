def obtener_noticias(zona: str) -> list:
    noticias = {
        "norte": ["Zona norte en valorización", "Nuevo metro cerca del norte"],
        "sur": ["Zona sur con alta demanda", "Inseguridad reportada en sur"],
        "centro": ["Centro con proyectos de renovación"],
    }
    return noticias.get(zona, ["Sin noticias recientes"])