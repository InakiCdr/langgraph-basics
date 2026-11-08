"""Paso 4 - Comparación: el mismo grafo con y sin el reducer add_messages.

Los dos grafos son idénticos: START -> nodo_1 -> nodo_2 -> END.
Cada nodo "responde" devolviendo un mensaje nuevo. Lo único que
cambia es cómo está declarado el campo messages en el State.

Las respuestas son fijas (sin LLM) para que la comparación sea
exacta y no dependa de lo que conteste el modelo.

Resultado: con add_messages quedan 3 mensajes; sin él, solo 1.
Una línea en el State decide si hay historial.

Ejecutar:  .venv/bin/python reducer_comparacion.py
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# State A: CON add_messages -> los mensajes devueltos se AÑADEN.
class StateConReducer(TypedDict):
    messages: Annotated[list, add_messages]


# State B: SIN reducer -> lo que devuelve un nodo SOBRESCRIBE el campo.
class StateSinReducer(TypedDict):
    messages: list


# Los mismos dos nodos para ambos grafos: cada uno devuelve solo su respuesta.
def nodo_1(state) -> dict:
    return {"messages": [AIMessage(content="Respuesta del nodo 1")]}


def nodo_2(state) -> dict:
    return {"messages": [AIMessage(content="Respuesta del nodo 2")]}


# Construye el mismo grafo para el State que le pasemos.
def construir(state_cls):
    builder = StateGraph(state_cls)
    builder.add_node("nodo_1", nodo_1)
    builder.add_node("nodo_2", nodo_2)
    builder.add_edge(START, "nodo_1")
    builder.add_edge("nodo_1", "nodo_2")
    builder.add_edge("nodo_2", END)
    return builder.compile()


def mostrar(titulo, resultado):
    print(f"--- {titulo}: {len(resultado['messages'])} mensajes ---")
    for m in resultado["messages"]:
        print(f"  [{m.type}] {m.content}")
    print()


if __name__ == "__main__":
    entrada = {"messages": [HumanMessage(content="Hola")]}

    mostrar("CON add_messages", construir(StateConReducer).invoke(entrada))
    mostrar("SIN add_messages", construir(StateSinReducer).invoke(entrada))
