"""Paso 8 - Mismo grafo, caminos distintos.

Reutilizamos el agente de agente_tools.py con dos preguntas:
- Una general  -> el modelo responde directamente:  chatbot -> END
- Una de pedido -> el modelo pide la tool:          chatbot -> tools -> chatbot -> END

El grafo no cambia: el camino lo decide el modelo en cada ejecución,
y la arista condicional (decidir) lo traduce en el siguiente nodo.

Ejecutar:  .venv/bin/python comparar_caminos.py
"""

from langchain_core.messages import HumanMessage

from agente_tools import graph

# Cada pregunta en su propio thread_id para que los historiales no se mezclen.
PREGUNTAS = [
    ("sin-tool", "¿Cuál es la capital de Francia?"),
    ("con-tool", "¿En qué estado está el pedido 5678?"),
]

for thread_id, pregunta in PREGUNTAS:
    config = {"configurable": {"thread_id": thread_id}}
    camino = ["START"]
    respuesta = ""

    print(f"=== {pregunta} ===")
    entrada = {"messages": [HumanMessage(content=pregunta)]}

    # stream(updates) emite un chunk por cada nodo ejecutado: así
    # reconstruimos el camino que ha seguido el grafo.
    for chunk in graph.stream(entrada, config, stream_mode="updates"):
        for nodo, update in chunk.items():
            camino.append(nodo)
            msg = update["messages"][-1]
            if nodo == "chatbot" and msg.tool_calls:
                tc = msg.tool_calls[0]
                print(f"  chatbot -> pide {tc['name']}({tc['args']})")
            elif nodo == "tools":
                print(f"  tools   -> {msg.content!r}")
            else:
                respuesta = msg.content
    camino.append("END")

    print(f"  Camino: {' -> '.join(camino)}  ({len(camino) - 2} nodos ejecutados)")
    print(f"  Respuesta: {respuesta}\n")
