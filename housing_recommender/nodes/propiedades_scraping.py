from services.scraping_client import obtener_propiedades

def propiedades_scraping(estado):
    props = obtener_propiedades(estado["criterios_actuales"])
    return {"propiedades_encontradas": props}