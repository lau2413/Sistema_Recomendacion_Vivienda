# Persona 2 - Adquisicion de datos

Esta parte queda desacoplada del grafo: cada nodo recibe `AgentState` o un
`dict` equivalente y devuelve un `dict` con unicamente los campos que modifica.
Los nodos no presentan resultados finales ni deciden el flujo global del grafo.

## Contrato con `state/models.py`

- `ajustar_requisitos`: lee `textoUsuario` y, si ya existe, `requisitos`.
  Devuelve `{"requisitos": ...}` con forma compatible con `Requisito`.
- `propiedades_scraping`: lee `requisitos`. Devuelve `{"propiedades": ...}`
  con elementos compatibles con `Propiedad`.
- `agente_noticias`: lee `propiedades` y opcionalmente `requisitos.ubicacion`.
  Devuelve `{"noticias": ...}` con elementos compatibles con `Noticia`.

## Servicios mockeables

- `services/requisitos_parser.py`: parser deterministico desde `textoUsuario`.
- `services/scraping_client.py`: wrapper de ofertas inmobiliarias. Por ahora
  usa `MockScrapingClient`, pero se puede reemplazar por un scraper real sin
  cambiar el nodo.
- `services/noticias_client.py`: wrapper de noticias/contexto urbano. Por ahora
  usa `MockNoticiasClient`, reemplazable por un cliente real.

Los wrappers quedan fuera de los nodos para que se puedan reemplazar o
monkeypatchear en pruebas sin cambiar la logica de LangGraph.
