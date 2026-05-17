from housing_recommender.nodes.agente_noticias import agente_noticias
from housing_recommender.nodes.ajustar_requisitos import ajustar_requisitos
from housing_recommender.nodes.construir_propuesta import construir_propuesta
from housing_recommender.nodes.propiedades_scraping import propiedades_scraping


def main() -> None:
    estado = {
        "textoUsuario": (
            "Busco apartamento en el sur, maximo 900000000 pesos, "
            "1 habitaciones, 1 baños"
        ),
        "requisitos": None,
        "propiedades": None,
        "noticias": None,
        "propuesta": None,
        "iteracion": 0,
        "max_iteraciones": 3,
    }

    estado.update(ajustar_requisitos(estado))
    estado.update(propiedades_scraping(estado))
    estado.update(agente_noticias(estado))
    estado.update(construir_propuesta(estado))

    print("REQUISITOS:")
    print(estado["requisitos"])

    print("\nPROPIEDADES:")
    print(estado["propiedades"])

    print("\nNOTICIAS:")
    print(estado["noticias"])

    print("\nPROPUESTA:")
    print(estado["propuesta"])


if __name__ == "__main__":
    main()
