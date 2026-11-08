"""Extra 4 - La arista condicional decide: con y sin tool.

Variación de comparar_caminos.py con dos mejoras:
1. Usamos tools_condition, la arista condicional que trae LangGraph
   (hace lo mismo que nuestra función decidir: tool_calls -> "tools",
   si no -> END). Imprimimos qué decide en cada pregunta.
2. Añadimos un mensaje de sistema. Sin él, llama3.1 con tools enlazadas
   suele negarse a responder preguntas generales ("solo sé de pedidos").

Ejecutar (desde langgraph-basics):  .venv/bin/python extras/paso4_sin_tool.py
Requiere Ollama con llama3.1.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

PEDIDOS = {"B200": "en reparto, llega mañana", "5678": "enviado, entrega estimada el viernes"}


@tool
def consulta_pedido(id_pedido: str) -> str:
    """Consulta el estado de un pedido a partir de su identificador."""
    return PEDIDOS.get(id_pedido.strip().upper(), f"No existe el pedido {id_pedido}")


tools = [consulta_pedido]
llm = ChatOllama(model="llama3.1").bind_tools(tools)

# El mensaje de sistema le aclara al modelo CUÁNDO usar la tool.
SISTEMA = SystemMessage(content=(
    "Eres un asistente general. Responde con normalidad a cualquier pregunta. "
    "Usa la herramienta consulta_pedido SOLO si te preguntan por un pedido."
))


class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State) -> dict:
    return {"messages": [llm.invoke([SISTEMA] + state["messages"])]}


def chatbot_con_traza(state: State) -> str:
    """Envuelve tools_condition solo para imprimir la decisión."""
    destino = tools_condition(state)
    print(f"  arista condicional -> {destino}")
    return destino


builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", chatbot_con_traza)   # -> "tools" o END
builder.add_edge("tools", "chatbot")
graph = builder.compile()

for pregunta in ["¿Cuál es la capital de Francia?", "¿En qué estado está el pedido 5678?"]:
    print(f"=== {pregunta} ===")
    resultado = graph.invoke({"messages": [HumanMessage(content=pregunta)]})
    camino = " -> ".join(m.type for m in resultado["messages"])
    print(f"  mensajes: {camino}")
    print(f"  respuesta: {resultado['messages'][-1].content}\n")
