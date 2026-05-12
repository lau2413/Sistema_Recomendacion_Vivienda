# Persona 2 - Adquisicion de datos

Esta parte queda desacoplada del grafo: cada nodo recibe `EstadoSistema` y
devuelve un `dict` con unicamente los campos que modifica. Los nodos no deben
presentar resultados finales ni decidir el flujo global del grafo.

## Nodos

- `ajustar_requisitos`: lee `texto_libre_usuario` y `criterios_actuales`.
  Devuelve unicamente
  `{"criterios_actuales": ...}`.
- `coordinar_sintetizador`: lee `criterios_actuales` y define zonas de busqueda.
  Devuelve unicamente `{"zonas_relevantes": ...}`.
- `agente_noticias`: lee `criterios_actuales.ciudad` y `zonas_relevantes`.
  Devuelve unicamente `{"contexto_noticias": ...}`.
- `propiedades_scraping`: lee `criterios_actuales`. Devuelve
  unicamente `{"propiedades_raw": ...}`.

## Servicios mockeables

- `services/requisitos_parser.py`: parser deterministico de preferencias desde
  texto plano.
- `services/noticias_client.py`: wrapper para contexto urbano/noticias.
- `services/scraping_client.py`: wrapper para fuentes inmobiliarias. Expone
  `buscar_propiedades` para uso real y `mock_propiedades` para pruebas.

Los wrappers quedan fuera de los nodos para que se puedan reemplazar o
monkeypatchear en pruebas sin cambiar la logica de LangGraph.
