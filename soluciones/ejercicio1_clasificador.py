"""Ejercicio 1 (solución de referencia) - Un grafo que clasifica y responde.

¡Inténtalo antes de mirar esta solución!

    START -> clasificar --(pregunta)--> responder_pregunta -> END
                        +--(queja)----> responder_queja ------> END

- clasificar: el LLM etiqueta el mensaje como "pregunta" o "queja" y
  guarda la etiqueta en el State (campo "tipo").
- La arista condicional lee state["tipo"] y elige el nodo de respuesta.
- Cada nodo de respuesta usa un mensaje de sistema distinto (tono distinto).

Ideas clave que practica:
- Un State con varios campos (no solo mensajes).
- Un nodo que NO responde al usuario, sino que decide (clasifica).
- Una arista condicional basada en un campo del State, no en tool_calls.

Ejecutar (desde langgraph-basics):  .venv/bin/python soluciones/ejercicio1_clasificador.py
Requiere Ollama con llama3.1.
"""

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

# temperature=0 para que la clasificación sea lo más estable posible.
llm = ChatOllama(model="llama3.1", temperature=0)


# 1. State: el mensaje del usuario, su tipo y la respuesta final.
class State(TypedDict):
    mensaje: str
    tipo: str
    respuesta: str


# 2. Nodo clasificador: pide al LLM UNA sola palabra y la normaliza.
def clasificar(state: State) -> dict:
    instruccion = SystemMessage(content=(
        "Clasifica el mensaje del cliente. Responde SOLO con una palabra: "
        "'pregunta' si pide información, o 'queja' si expresa un problema "
        "o insatisfacción."
    ))
    salida = llm.invoke([instruccion, HumanMessage(content=state["mensaje"])])
    # Los LLM no siempre obedecen al pie de la letra: normalizamos.
    tipo = "queja" if "queja" in salida.content.lower() else "pregunta"
    return {"tipo": tipo}


# 3. Nodos de respuesta: mismo LLM, distinto "papel".
def responder_pregunta(state: State) -> dict:
    sistema = SystemMessage(content="Eres un asistente informativo. Responde en 2 frases, claro y directo.")
    r = llm.invoke([sistema, HumanMessage(content=state["mensaje"])])
    return {"respuesta": r.content}


def responder_queja(state: State) -> dict:
    sistema = SystemMessage(content=(
        "Eres el servicio de atención al cliente. Pide disculpas con empatía, "
        "reconoce el problema y propone un siguiente paso concreto. Máximo 3 frases."
    ))
    r = llm.invoke([sistema, HumanMessage(content=state["mensaje"])])
    return {"respuesta": r.content}


# 4. Arista condicional: lee el campo "tipo" y devuelve el nodo destino.
#    El Literal documenta los destinos posibles (y ayuda al dibujar el grafo).
def enrutar(state: State) -> Literal["responder_pregunta", "responder_queja"]:
    return "responder_queja" if state["tipo"] == "queja" else "responder_pregunta"


# 5. Grafo.
builder = StateGraph(State)
builder.add_node("clasificar", clasificar)
builder.add_node("responder_pregunta", responder_pregunta)
builder.add_node("responder_queja", responder_queja)

builder.add_edge(START, "clasificar")
builder.add_conditional_edges("clasificar", enrutar)
builder.add_edge("responder_pregunta", END)
builder.add_edge("responder_queja", END)
graph = builder.compile()


if __name__ == "__main__":
    # Dibujo del grafo junto a este script (necesita internet: mermaid.ink).
    # Las flechas punteadas desde clasificar son la arista condicional.
    from pathlib import Path
    ruta_png = Path(__file__).with_name("grafo_clasificador.png")
    ruta_png.write_bytes(graph.get_graph().draw_mermaid_png())
    print(f"Imagen guardada en {ruta_png.name}\n")

    mensajes = [
        "¿Cuál es el horario de atención de la tienda?",
        "Mi pedido llegó roto y nadie me contesta los correos. Estoy harto.",
        "¿Hacéis envíos a Portugal?",
    ]
    for texto in mensajes:
        # stream(updates) para ver el camino: clasificar -> nodo elegido.
        camino = []
        final = {}
        for chunk in graph.stream({"mensaje": texto}, stream_mode="updates"):
            for nodo, update in chunk.items():
                camino.append(nodo)
                final.update(update)
        print(f"Mensaje:   {texto}")
        print(f"Tipo:      {final['tipo']}")
        print(f"Camino:    START -> {' -> '.join(camino)} -> END")
        print(f"Respuesta: {final['respuesta']}\n")
