"""Paso 1 - Primer StateGraph: un State con un campo y dos nodos encadenados.

    START -> mayusculas -> exclamar -> END

Idea clave: un grafo es un State que va pasando por nodos. Cada nodo
lee el state, hace su trabajo y devuelve SOLO los campos que cambia.
Entrada 'hola langgraph' -> salida 'HOLA LANGGRAPH!!!'.

Ejecutar:  .venv/bin/python grafo_basico.py
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# 1. El State: un diccionario tipado que viaja por el grafo.
#    Es la "memoria de trabajo" compartida por todos los nodos.
class State(TypedDict):
    mensaje: str


# 2. Los nodos: funciones que reciben el state y devuelven
#    un dict con los campos que quieren actualizar.
def mayusculas(state: State) -> dict:
    return {"mensaje": state["mensaje"].upper()}


def exclamar(state: State) -> dict:
    return {"mensaje": state["mensaje"] + "!!!"}


# 3. Construir el grafo: añadir nodos y conectar las aristas.
#    START y END son nodos especiales: entrada y salida del grafo.
#    add_edge(a, b) = "cuando termine a, ejecuta b" (arista fija).
builder = StateGraph(State)
builder.add_node("mayusculas", mayusculas)
builder.add_node("exclamar", exclamar)

builder.add_edge(START, "mayusculas")
builder.add_edge("mayusculas", "exclamar")
builder.add_edge("exclamar", END)

# 4. Compilar: valida la estructura y devuelve un grafo ejecutable.
graph = builder.compile()


if __name__ == "__main__":
    # 5. Invocar con un state inicial.
    resultado = graph.invoke({"mensaje": "hola langgraph"})
    print("State final:", resultado)

    # 6. Dibujar el grafo. draw_mermaid_png usa por defecto el servicio
    #    web mermaid.ink, así que necesita conexión a internet.
    png = graph.get_graph().draw_mermaid_png()
    with open("grafo.png", "wb") as f:
        f.write(png)
    print("Imagen guardada en grafo.png")
