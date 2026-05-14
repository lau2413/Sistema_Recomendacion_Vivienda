# prueba_nodo.py (archivo temporal de prueba)
from state.models import AgentState
from nodes.interpretar_requisitos import interpretar_requisitos

# Caso de prueba 1: una frase típica
state_inicial = AgentState(
    textoUsuario="Busco un apartamento de 3 habitaciones en El Poblado, "
                 "máximo 500 millones, con 3 parqueaderos y al menos 80 metros cuadrados."
)

resultado = interpretar_requisitos(state_inicial)
print("=" * 60)
print("REQUISITOS EXTRAÍDOS:")
print("=" * 60)
print(resultado["requisitos"].model_dump_json(indent=2))

