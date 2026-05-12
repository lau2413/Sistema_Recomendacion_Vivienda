from services.noticias_client import obtener_noticias

def agente_noticias(estado):
    zonas = set(p["zona"] for p in estado["propiedades_encontradas"])
    contexto = {}
    for zona in zonas:
        contexto[zona] = obtener_noticias(zona)
    return {"zonas_analizadas": contexto}