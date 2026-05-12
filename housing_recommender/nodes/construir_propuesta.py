def construir_propuesta(estado):
    criterios = estado["criterios_actuales"]
    props = estado["propiedades_encontradas"]
    
    filtradas = [
        p for p in props
        if p["precio"] <= criterios.get("precio_max", 9999999)
        and p["area"] >= criterios.get("area_min", 0)
        and (criterios.get("tipo") is None or p["tipo"] == criterios["tipo"])
    ]
    return {"propiedades_filtradas": filtradas}