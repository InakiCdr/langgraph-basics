"""Paso 6 - Inspecciona los checkpoints que guarda el MemorySaver en un thread.

Tras 2 turnos de conversación, get_state_history(config) devuelve
todos los snapshots guardados para ese thread (del más reciente al
más antiguo). De cada uno mostramos:
- step:    número de paso dentro del thread
- origen:  metadata["source"] -> "input" (entra el mensaje del usuario)
           o "loop" (estado tras ejecutar nodos del grafo)
- mensajes: cuántos mensajes había en el state en ese punto
- siguiente: qué nodo(s) tocaba ejecutar a continuación (() = ninguno)

Resultado: 2 turnos = 6 checkpoints (3 por turno). Hay una foto del
state antes y después de cada nodo; el campo "siguiente" es lo que
permite reanudar la ejecución si algo se cae a mitad.

Ejecutar:  .venv/bin/python historial_checkpoints.py  (requiere Ollama)
"""

from langchain_core.messages import HumanMessage

from chatbot_memoria import graph

config = {"configurable": {"thread_id": "historial"}}

for texto in ["Hola, me llamo Lucía.", "¿Cómo me llamo?"]:
    resultado = graph.invoke({"messages": [HumanMessage(content=texto)]}, config)
    print(f"Usuario: {texto}")
    print(f"Bot:     {resultado['messages'][-1].content}\n")

# Lo mostramos en orden cronológico (get_state_history va del último al primero).
historial = list(graph.get_state_history(config))[::-1]

print(f"Checkpoints guardados en el thread: {len(historial)}\n")
print(f"{'step':>4} | {'origen':<6} | {'mensajes':>8} | siguiente")
print("-" * 40)
for snap in historial:
    step = snap.metadata.get("step")
    origen = snap.metadata.get("source")
    n_mensajes = len(snap.values.get("messages", []))
    siguiente = snap.next if snap.next else "(fin)"
    print(f"{step:>4} | {origen:<6} | {n_mensajes:>8} | {siguiente}")
