"""Extra 2 - ¿Qué pasa si quitas add_messages en un chatbot CON memoria?

En reducer_comparacion.py vimos que, sin reducer, cada nodo sustituye la
lista. Aquí lo llevamos a un caso real: el chatbot con checkpointer.

Sin add_messages, en cada turno el mensaje nuevo que enviamos SUSTITUYE
al historial guardado. El checkpointer sigue funcionando, pero lo que
guarda se pisa: el modelo solo ve el último mensaje y "olvida" el nombre.

Mismo código, misma conversación, dos States:
- CON add_messages -> recuerda.
- SIN add_messages -> olvida.

Ejecutar (desde langgraph-basics):  .venv/bin/python extras/paso2_sin_reducer.py
Requiere Ollama con llama3.1.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

llm = ChatOllama(model="llama3.1")


class StateConReducer(TypedDict):
    messages: Annotated[list, add_messages]


class StateSinReducer(TypedDict):
    messages: list            # <- la única línea que cambia


def chatbot(state) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}


def construir(state_cls):
    builder = StateGraph(state_cls)
    builder.add_node("chatbot", chatbot)
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)
    return builder.compile(checkpointer=MemorySaver())


TURNOS = ["Hola, me llamo Lucía.", "¿Cómo me llamo?"]

for titulo, state_cls in [("CON add_messages", StateConReducer),
                          ("SIN add_messages", StateSinReducer)]:
    graph = construir(state_cls)
    config = {"configurable": {"thread_id": "1"}}
    print(f"=== {titulo} ===")
    for texto in TURNOS:
        resultado = graph.invoke({"messages": [HumanMessage(content=texto)]}, config)
        print(f"  Usuario: {texto}")
        print(f"  Bot:     {resultado['messages'][-1].content}")
        print(f"  (mensajes guardados en el thread: {len(resultado['messages'])})\n")
