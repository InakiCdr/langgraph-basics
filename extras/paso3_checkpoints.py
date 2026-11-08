"""Extra 3 - El checkpointer guarda una foto del State en cada paso.

En historial_checkpoints.py contamos mensajes. Aquí usamos el grafo
sencillo (mayusculas -> exclamar) para ver el CONTENIDO de cada foto:
cómo va cambiando "mensaje" checkpoint a checkpoint.

Después, "viajamos en el tiempo": volvemos a ejecutar el grafo desde
un checkpoint intermedio (antes de exclamar) pasando su config. Es la
misma mecánica que permite reanudar si algo se cae a mitad.

Ejecutar (desde langgraph-basics):  .venv/bin/python extras/paso3_checkpoints.py
No usa el LLM.
"""

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    mensaje: str


def mayusculas(state: State) -> dict:
    return {"mensaje": state["mensaje"].upper()}


def exclamar(state: State) -> dict:
    return {"mensaje": state["mensaje"] + "!!!"}


builder = StateGraph(State)
builder.add_node("mayusculas", mayusculas)
builder.add_node("exclamar", exclamar)
builder.add_edge(START, "mayusculas")
builder.add_edge("mayusculas", "exclamar")
builder.add_edge("exclamar", END)
graph = builder.compile(checkpointer=MemorySaver())

config = {"configurable": {"thread_id": "fotos"}}
graph.invoke({"mensaje": "hola langgraph"}, config)

# get_state_history va del más reciente al más antiguo: lo invertimos.
historial = list(graph.get_state_history(config))[::-1]

print(f"Fotos guardadas: {len(historial)}\n")
print(f"{'step':>4} | {'siguiente':<16} | state")
print("-" * 55)
for snap in historial:
    siguiente = ", ".join(snap.next) if snap.next else "(fin)"
    print(f"{snap.metadata['step']:>4} | {siguiente:<16} | {snap.values}")

# --- Reanudar desde una foto intermedia --------------------------------
# Buscamos la foto en la que lo siguiente era "exclamar".
antes_de_exclamar = next(s for s in historial if s.next == ("exclamar",))
print(f"\nReanudando desde step {antes_de_exclamar.metadata['step']}"
      f" (state = {antes_de_exclamar.values}) ...")

# invoke(None, config_de_esa_foto) = "continúa desde aquí". Solo se
# ejecuta lo que faltaba: el nodo exclamar.
resultado = graph.invoke(None, antes_de_exclamar.config)
print(f"Resultado: {resultado}")
