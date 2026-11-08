"""Paso 5 - El chatbot de chatbot.py, ahora con memoria entre invocaciones.

- Reutilizamos el mismo builder (State con add_messages + nodo chatbot).
- Lo compilamos con un checkpointer MemorySaver: guarda el state
  al final de cada invocación, indexado por thread_id.
- En cada invoke solo enviamos el mensaje NUEVO; el checkpointer
  recupera el historial de ese thread y add_messages lo acumula.
- Distinto thread_id = conversación distinta, sin memoria compartida.

Es la forma actual de dar memoria (sustituye a ConversationBufferMemory
y similares, que están deprecadas). MemorySaver guarda en RAM: al
terminar el proceso se pierde. En producción: SqliteSaver/PostgresSaver.

Ejecutar:  .venv/bin/python chatbot_memoria.py  (requiere Ollama)
"""

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from chatbot import builder

# Mismo builder del paso 3; lo único que cambia es el checkpointer.
graph = builder.compile(checkpointer=MemorySaver())


def turno(texto: str, thread_id: str) -> None:
    # El thread_id identifica la conversación en el checkpointer.
    config = {"configurable": {"thread_id": thread_id}}
    # Solo enviamos el mensaje nuevo: el historial lo pone el checkpointer.
    resultado = graph.invoke({"messages": [HumanMessage(content=texto)]}, config)
    print(f"[thread {thread_id}] Usuario: {texto}")
    print(f"[thread {thread_id}] Bot:     {resultado['messages'][-1].content}")
    print(f"[thread {thread_id}] Mensajes guardados en este thread: {len(resultado['messages'])}\n")


if __name__ == "__main__":
    print("### Mismo thread_id ('1') en 3 turnos ###\n")
    turno("Hola, me llamo Lucía.", "1")
    turno("Mi deporte favorito es el ciclismo.", "1")
    turno("¿Cómo me llamo y cuál es mi deporte favorito?", "1")

    print("### Otro thread_id ('2'): no comparte memoria ###\n")
    turno("¿Cómo me llamo y cuál es mi deporte favorito?", "2")
