"""Paso 3 - El grafo evoluciona a chatbot: START -> chatbot -> END.

Cambios respecto a grafo_basico.py:
- El State ya no guarda un texto, sino una LISTA de mensajes.
- add_messages es un "reducer": en vez de sustituir la lista,
  AÑADE los mensajes que devuelve cada nodo a los que ya había.
- El nodo llama a un LLM local (Ollama con llama3.1).

Qué observar: el grafo funciona, pero el modelo no conoce LangGraph
y se inventa la respuesta con total seguridad (alucinación).

Ejecutar:  .venv/bin/python chatbot.py  (requiere Ollama en marcha)
"""

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# 1. State: lista de mensajes que se acumula gracias a add_messages.
#    Annotated[tipo, reducer] le dice a LangGraph CÓMO combinar lo que
#    devuelve un nodo con lo que ya había en ese campo.
class State(TypedDict):
    messages: Annotated[list, add_messages]


# 2. El modelo local.
llm = ChatOllama(model="llama3.1")


# 3. Nodo chatbot: pasa toda la conversación al LLM y devuelve
#    SOLO la respuesta nueva; add_messages se encarga de añadirla.
def chatbot(state: State) -> dict:
    respuesta = llm.invoke(state["messages"])
    return {"messages": [respuesta]}


# 4. Grafo: START -> chatbot -> END
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile()


if __name__ == "__main__":
    pregunta = "Explícame en dos frases qué es LangGraph."
    resultado = graph.invoke({"messages": [HumanMessage(content=pregunta)]})

    # El state final contiene la conversación completa: pregunta + respuesta.
    print(f"Mensajes en el state: {len(resultado['messages'])}\n")
    for m in resultado["messages"]:
        print(f"[{m.type}] {m.content}\n")
