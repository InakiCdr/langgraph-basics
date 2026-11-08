"""Extra 1 - Ver el State COMPLETO después de cada nodo con stream.

En stream_updates.py usamos stream_mode="updates": solo lo que devuelve
cada nodo. Aquí comparamos con stream_mode="values": el state entero
tras cada paso (incluido el state inicial, antes de ejecutar ningún nodo).

Para que se note la diferencia, el State tiene DOS campos y los nodos
solo tocan "mensaje" ("original" no lo modifica nadie):
- "updates" muestra únicamente el campo que cambia.
- "values" muestra siempre los dos campos.

Ejecutar (desde langgraph-basics):  .venv/bin/python extras/paso1_stream.py
No usa el LLM.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    mensaje: str      # lo transforman los nodos
    original: str     # nadie lo toca: solo aparece en "values"


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
graph = builder.compile()

entrada = {"mensaje": "hola langgraph", "original": "hola langgraph"}

print('--- stream_mode="updates": solo lo que devuelve cada nodo ---')
for chunk in graph.stream(entrada, stream_mode="updates"):
    print(" ", chunk)

print('\n--- stream_mode="values": el State completo tras cada paso ---')
for i, state in enumerate(graph.stream(entrada, stream_mode="values")):
    etiqueta = "state inicial" if i == 0 else f"tras el nodo {i}"
    print(f"  {etiqueta:<14} -> {state}")
