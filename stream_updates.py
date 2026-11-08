"""Paso 2 - Ver el grafo por dentro con stream.

Ejecuta el grafo de grafo_basico.py con stream en modo "updates".

En este modo, cada paso emite un dict {nombre_nodo: actualización},
es decir, solo lo que ese nodo ha devuelto (no el state completo).
Con invoke() solo veríamos el resultado final; con stream() vemos
el orden de ejecución: primero mayusculas y luego exclamar.
(Otros modos: "values" emite el state completo tras cada paso.)

Ejecutar:  .venv/bin/python stream_updates.py
"""

# Importamos el grafo ya compilado del paso 1 (no se ejecuta su main).
from grafo_basico import graph

entrada = {"mensaje": "hola langgraph"}
print("Entrada:", entrada)

for paso, chunk in enumerate(graph.stream(entrada, stream_mode="updates"), start=1):
    for nodo, actualizacion in chunk.items():
        print(f"Paso {paso} | nodo '{nodo}' devuelve: {actualizacion}")
