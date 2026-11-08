"""Paso 9 - Visualización final del grafo completo (agente con tools + memoria).

get_graph() devuelve la estructura del grafo compilado y draw_mermaid_png()
la dibuja como PNG. Cómo leer la imagen:
- Flechas continuas  = aristas fijas (add_edge): siempre se recorren.
- Flechas punteadas  = arista condicional (add_conditional_edges): el
  camino se decide en tiempo de ejecución (tools o __end__).
- La flecha tools -> chatbot cierra el ciclo del agente.

Nota: draw_mermaid_png usa por defecto el servicio web mermaid.ink, así que
necesita conexión a internet. Sin conexión, imprimimos el código Mermaid
(se puede pegar en https://mermaid.live para verlo).

Ejecutar:  .venv/bin/python visualizar_grafo.py   (no llama al modelo)
"""

from agente_tools import graph

estructura = graph.get_graph()

try:
    png = estructura.draw_mermaid_png()
    with open("grafo_completo.png", "wb") as f:
        f.write(png)
    print("Imagen guardada en grafo_completo.png")
except Exception as error:  # p. ej. sin conexión a internet
    print(f"No se pudo generar el PNG ({error}). Código Mermaid:\n")
    print(estructura.draw_mermaid())
