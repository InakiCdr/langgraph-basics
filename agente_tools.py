"""Paso 7 - Agente con herramientas y memoria.

El grafo completo de la práctica:

    START -> chatbot --(¿pide tool?)-- sí --> tools -> chatbot -> ...
                     +---------------- no --> END

Piezas nuevas respecto a chatbot_memoria.py:
- @tool consulta_pedido: una función Python que el modelo puede "pedir" usar.
- bind_tools: le describe al modelo qué tools existen (nombre, args, docstring).
- ToolNode: nodo ya hecho que ejecuta las tool_calls del último mensaje.
- Arista condicional: decide en tiempo de ejecución si ir a "tools" o a END.
- Ciclo tools -> chatbot: tras ejecutar la tool, el modelo vuelve a hablar
  con el resultado ya en el historial.

Ejecutar:  .venv/bin/python agente_tools.py
"""

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# ---------------------------------------------------------------------------
# 1. Datos de ejemplo: hacen el papel de una base de datos de pedidos.
# ---------------------------------------------------------------------------
PEDIDOS = {
    "A100": "entregado el 3 de noviembre",
    "B200": "en reparto, llega mañana",
    "C300": "retrasado en aduanas",
    "5678": "enviado, entrega estimada el viernes",
}


# ---------------------------------------------------------------------------
# 2. La tool.
#    @tool convierte la función en una herramienta: su nombre, sus argumentos
#    (con tipos) y su DOCSTRING se envían al modelo. El modelo NO ejecuta
#    nada: solo decide "quiero llamar a consulta_pedido con id_pedido=X".
#    Quien la ejecuta de verdad es el ToolNode.
# ---------------------------------------------------------------------------
@tool
def consulta_pedido(id_pedido: str) -> str:
    """Consulta el estado de un pedido a partir de su identificador (p. ej. 'B200')."""
    estado = PEDIDOS.get(id_pedido.strip().upper())
    return estado if estado else f"No existe ningún pedido con id {id_pedido}"


tools = [consulta_pedido]


# ---------------------------------------------------------------------------
# 3. State: el historial de mensajes. add_messages hace que cada nodo AÑADA
#    mensajes en vez de sustituir la lista (ver reducer_comparacion.py).
#    Aquí acabarán mensajes de 4 tipos: human, ai, ai con tool_calls y tool.
# ---------------------------------------------------------------------------
class State(TypedDict):
    messages: Annotated[list, add_messages]


# ---------------------------------------------------------------------------
# 4. El modelo, con las tools "enlazadas". A partir de aquí su respuesta
#    puede ser texto normal o una petición de tool (msg.tool_calls).
# ---------------------------------------------------------------------------
# temperature=0: respuestas más deterministas, y así la decisión de usar
# o no la tool es estable entre ejecuciones (con llama3.1 se nota mucho).
modelo_base = ChatOllama(model="llama3.1", temperature=0)
llm = modelo_base.bind_tools(tools)

# Mensaje de sistema: aclara CUÁNDO usar la tool.
# No se guarda en el State: se antepone en cada llamada al modelo.
SISTEMA = SystemMessage(content=(
    "Eres un asistente general. Responde con normalidad a cualquier pregunta. "
    "Usa la herramienta consulta_pedido SOLO si te preguntan por un pedido."
))


# Nodo chatbot: le pasa TODO el historial al modelo y devuelve solo su
# mensaje nuevo (add_messages se encarga de añadirlo al state).
def chatbot(state: State) -> dict:
    respuesta = llm.invoke([SISTEMA] + state["messages"])

    # Truco para modelos pequeños: llama3.1 con tools enlazadas DECIDE bien
    # si usar o no la tool, pero cuando no la usa suele contestar mal
    # ("no tengo una función para eso"). Si no ha pedido tool y venimos de
    # una pregunta del usuario, repetimos la llamada SIN tools para que
    # responda con normalidad. El camino del grafo no cambia.
    if not respuesta.tool_calls and state["messages"][-1].type == "human":
        respuesta = modelo_base.invoke(state["messages"])

    return {"messages": [respuesta]}


# ---------------------------------------------------------------------------
# 5. Arista condicional: una función que mira el state y devuelve el NOMBRE
#    del siguiente nodo. Es el "if" del grafo.
#    (LangGraph trae una equivalente lista para usar: prebuilt.tools_condition.)
# ---------------------------------------------------------------------------
def decidir(state: State) -> str:
    ultimo = state["messages"][-1]
    return "tools" if ultimo.tool_calls else END


# ---------------------------------------------------------------------------
# 6. Montar el grafo.
# ---------------------------------------------------------------------------
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))      # ejecuta las tool_calls

builder.add_edge(START, "chatbot")              # siempre se empieza por el modelo
builder.add_conditional_edges(                  # desde chatbot hay dos salidas posibles
    "chatbot", decidir, ["tools", END]
)
builder.add_edge("tools", "chatbot")            # tras la tool, vuelta al modelo (ciclo)

# ---------------------------------------------------------------------------
# 7. Compilar con checkpointer: el state se guarda tras cada paso, por
#    thread_id. Así el agente recuerda turnos anteriores (y se puede reanudar).
# ---------------------------------------------------------------------------
graph = builder.compile(checkpointer=MemorySaver())


def turno(pregunta: str, config: dict, n: int) -> None:
    """Lanza un turno con stream(updates) e imprime qué hace cada nodo."""
    print(f"--- Turno {n} ---")
    print(f"Usuario: {pregunta}")
    entrada = {"messages": [HumanMessage(content=pregunta)]}
    for paso, chunk in enumerate(graph.stream(entrada, config, stream_mode="updates"), start=1):
        for nodo, update in chunk.items():
            msg = update["messages"][-1]
            if nodo == "chatbot" and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"Paso {paso} | chatbot -> pide tool {tc['name']}({tc['args']})")
            elif nodo == "chatbot":
                print(f"Paso {paso} | chatbot -> respuesta final: {msg.content}")
            else:
                print(f"Paso {paso} | tools   -> {msg.name} devuelve: {msg.content!r}")
    print()


if __name__ == "__main__":
    # Mismo thread_id en los dos turnos -> comparten memoria.
    config = {"configurable": {"thread_id": "cliente-1"}}

    # Turno 1: damos el número de pedido -> ciclo chatbot -> tools -> chatbot.
    turno("¿En qué estado está mi pedido B200?", config, 1)

    # Turno 2: NO damos el número; el modelo lo saca del historial que
    # recupera el checkpointer. Tools y memoria trabajando juntos.
    turno("Vuelve a consultar mi pedido, ¿sigue igual?", config, 2)
