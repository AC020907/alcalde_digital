# Guía de sustentación: Civitas / Alcalde Digital

Según la rúbrica (§20, pp. 13–14), cualquier integrante puede ser interrogado sobre cualquier parte del proyecto. Las respuestas de esta guía remiten a código real: ábrelo mientras estudias.

## 1. El juego en 30 segundos

Civitas tiene dos modos con el mismo tema: Ciudad Nova vota alcalde y la red social Civitas se llena de rumores.

- **Historia / Modo Feria** (un jugador): novela visual. Eres el alcalde, investigas con Claudia quién fabrica los rumores (NOVA), superas cinco retos y llegas a uno de cinco finales.
- **Arena Civitas** (2–4 jugadores, LAN): cada uno elige un rol (Ciudadano, Periodista, Influencer o Candidato).
  - En 5 rondas llega una publicación y todos deciden a la vez, contra el reloj, qué hacer con ella.
  - El servidor la propaga por el grafo social, mueve los indicadores y reparte puntos.
  - Al final, los ciudadanos votan entre cuatro candidatos.

## 2. Las preguntas de la página 15 del PDF

**¿Por qué utilizaron un árbol?**
- Cada publicación ofrece decisiones encadenadas: verificar lleva a la pregunta «¿Es verdadera?», y esta a compartir con la fuente o reportar.
- Es jerárquico y sin ciclos: un árbol general (n-ario). La ruta raíz → hoja es la decisión completa; la hoja trae la consecuencia.
- Archivos: `game/clases/Tree.py` y `game/clases/arena/reglas.py`, funciones `arbol_base()` y `arbol_para()`.

**¿Por qué utilizaron un grafo?**
- Las relaciones de quién sigue a quién no son jerárquicas: hay ciclos (Carlos ↔ María) y nodos con muchos seguidores (el influencer).
- Un grafo dirigido y ponderado modela «lo que publica A le llega a B con fuerza w». Además está el grafo de zonas de la ciudad.
- Archivo: `game/clases/GrafoSocial.py`.

**¿Qué problema resuelve cada estructura?**
- **Árbol:** qué puede hacer cada jugador y qué consecuencia tiene su elección. Además, el servidor **valida** la ruta recibida recorriendo el árbol (`recorrer_ruta`).
- **Grafo social:** a quién llega una publicación, cuántos la reciben y en cuántos saltos (BFS multifuente).
- **Grafo de la ciudad:** dónde empieza el boca a boca (BFS de distancias de zona).
- **AVL** (historia): sacar en orden de riesgo las publicaciones del teléfono.

**¿Cómo afectan estas estructuras las decisiones del jugador?**
- El rol modifica el árbol: el Candidato no tiene «Reportar» cuando hablan de su campaña (se **elimina** la rama) y en su lugar tiene «Responder con datos» (se **inserta**).
- La hoja elegida decide si el jugador es **fuente** del BFS (compartir) o **bloquea** a sus seguidores (reportar).

**¿Qué ocurre cuando cambia la información o las relaciones?**
- Si una publicación resulta falsa y se desmintió, sus efectos negativos bajan al 40 %.
- Si dos jugadores reportan, Civitas la retira y su autor casi no propaga.
- Cuando un jugador entra a la sala, su cuenta se agrega como vértice con aristas según su rol; si sale del lobby, se elimina con todas sus aristas (`eliminar_usuario`).
- La confianza de cada ciudadano en cada candidato cambia según lo que le llegó, y eso cambia los votos.

**¿Cómo se comunica la información entre los jugadores?**
- Cliente-servidor por **sockets TCP**, un mensaje JSON por línea, protocolo versionado. El servidor es autoritativo: los clientes solo mandan la ruta elegida y el servidor decide todo lo demás.
- Ver `docs/ARQUITECTURA_MULTIJUGADOR.md`.

**¿Qué comportamiento responsable busca fomentar?**
- Verificar antes de compartir, no amplificar rumores, no censurar opiniones (reportarlas también resta convivencia) y responder a críticas con datos.
- Entender que quien tiene más alcance (el influencer) tiene más responsabilidad.

## 3. Preguntas probables del jurado (con respuesta verificada)

| Pregunta | Respuesta |
|---|---|
| ¿Cómo se inserta y se elimina en el árbol? | `insertar_hijo(padre, …)` añade el hijo y enlaza `padre`, en O(1). `eliminar(nodo)` lo quita de la lista de hijos de su padre, con todo su subárbol. Se usa en `arbol_para` con el rol Candidato. |
| ¿Qué recorridos tiene? | Preorden y posorden (recursivos), por niveles (BFS con cola) y `recorrer_ruta`. Prueba: `TestArbol`. |
| ¿Qué variante de árbol es? | General (n-ario), porque los nodos tienen 2, 4 o 5 hijos. En la historia también hay un AVL (`ArbolAVL.py`) ordenado por riesgo, con rotaciones. |
| ¿El grafo es dirigido? ¿Ponderado? ¿Por qué? | Las dos cosas. Seguir no es recíproco, y la fuerza de cada vínculo es la probabilidad de que la publicación cruce (`se_propaga`). |
| ¿Qué algoritmo propaga? | BFS multifuente (`bfs_multifuente`): las fuentes son el autor, quienes compartieron y los vecinos de la zona; los bloqueados son los protegidos por reportes. Cuesta O(V+E). |
| ¿Por qué BFS y no DFS? | La propagación avanza por oleadas: el nivel equivale al número de «saltos», que mide la velocidad. El DFS se usa en la historia para reconstruir la cadena hacia el origen (Rastreador). |
| ¿Cómo evitan bucles infinitos? | Con el conjunto `visitados` en BFS y DFS. Prueba: `test_grafo_social_del_pdf_y_ciclos`. |
| ¿El azar no decide todo? | El azar decide qué publicación y qué evento salen, y con qué probabilidad cruza cada arista. Lo que se propaga y lo que se frena lo deciden los jugadores. Con la misma semilla, misma partida (pruebas reproducibles). |
| ¿Qué pasa si un cliente manda puntos falsos? | Se ignoran: el protocolo descarta los campos desconocidos y los puntos solo los calcula el servidor. Prueba: `test_id_repetido_no_duplica_y_puntos_del_cliente_se_ignoran`. |
| ¿Y si alguien se desconecta? | En el lobby libera su rol. En juego conserva el puesto y la ronda no se bloquea; con su token vuelve al mismo puesto. Prueba: `test_desconexion_y_reconexion_con_token`. |
| ¿Cómo sincronizan? | El servidor difunde `estado`, `ronda`, `resultado` y `final` con número de secuencia. Prueba: 2, 3 y 4 clientes en procesos separados terminan con exactamente el mismo resultado. |
| ¿Por qué funciona sin internet? | El servidor corre en un equipo del salón. La clasificación online (Render + Neon) es solo de la historia y es opcional. |
| ¿Funciona en la web? | La historia sí. La Arena no, porque los navegadores no abren sockets TCP; muestra un aviso para usar la versión de escritorio. |
| ¿Cómo se decide la elección? | Cada ciudadano vota al candidato en quien más confía. Esa confianza la cambian las publicaciones que le llegaron (rumores sin desmentir restan; desmentidos y propuestas verificadas suman), más la reputación del jugador Candidato. La participación decide cuántos votan. |
| ¿Qué componente inclusivo tienen y para qué? | Avisos visuales de sonido (para quien no oye o juega sin audio), subtítulos siempre visibles, reducir movimiento (mareo) y formas además de colores (daltonismo). |

## 3b. Preguntas sobre los cambios recientes

| Pregunta | Respuesta |
|---|---|
| ¿Qué pasa si verifico mal? | Resta. Reportar como falsa una noticia verdadera baja la confianza y tu reputación; dar por cierto un rumor falso sube la desinformación. Se comprueba en los dos modos (`tests/test_coherencia_educativa.py`). |
| ¿Cómo sabe el jugador si es verdadera? | Al pulsar «Verificar» aparece lo que encuentra: la fuente, la fecha o si el documento existe. El periodista de la Arena ve la fuente real. |
| ¿Hay elecciones en la historia? | Sí. El domingo se nombran los cuatro candidatos y, antes del resultado final, el **escrutinio** muestra votos, participación, abstención y por qué, a partir de los indicadores y tu credibilidad (`clases/Eleccion.py`). |
| ¿Se pueden pausar los minijuegos? | Sí. Moderación, Caza-Rumores y Rastreador comparten una pausa que detiene el reloj (`minijuegos/pausa.rpy`). El Duelo y la Ruta de la Verdad tienen la suya. |
| ¿La Ruta de la Verdad cambia la historia? | Sí. Claudia reacciona según cuántas evidencias recuperaste y ajusta información verificada y confianza (`label evidencias_rescatadas`). |
| ¿Y la Arena Online? | Es una mejora para la feria: el mismo motor de reglas en el servidor de Render, jugado desde el navegador por HTTPS. El requisito de sockets (§13) lo cumple la Arena local. |

## 4. Guion de demostración (3–5 minutos)

1. **(30 s) Contexto.** Menú principal: Ciudad Nova, elecciones, la red Civitas. Abrir **Ayuda → Objetivo** y **Roles**.
2. **(45 s) Sala.** En el PC 1: «Arena (2-4 jugadores)» → «Crear sala». Se ve la IP. En el PC 2 (y 3–4): «Unirse» con esa IP; cada uno elige un rol distinto. Si falta gente, «Añadir jugador automático».
3. **(90 s) Una ronda completa.**
   - Mostrar la publicación, el evento aleatorio y el **reloj**.
   - El Periodista pulsa **Verificar** y ve la fuente real; el Ciudadano solo ve una pista (el árbol cambia por rol).
   - Uno comparte y otro reporta.
   - **Resultado:** era falsa; llegó a X ciudadanos en Y saltos; las flechas son el **BFS** y los azules están **protegidos** por el reporte. Los indicadores cambian arriba y aparece el logro.
4. **(45 s) Explicar las estructuras sobre la pantalla.** Árbol: «Verificar → ¿Es verdadera? → No: reportarla» es una ruta raíz → hoja. Grafo: las zonas (grafo de la ciudad) y las flechas (grafo social).
5. **(45 s) Elección.** Votos por candidato, «¿Por qué ganó?», resultado de la ciudad y puntuación individual con logros.
6. **(30 s) Cierre.** «Verificar frena rumores, reportar opiniones también daña y el influencer pesa el doble.» Pregunta al público.

Si la LAN falla, ejecutar en un PC `python tests/qa_visual.py arena --salida demo`, que juega con 2 Ren'Py y 2 bots en procesos separados, o mostrar las capturas de `docs/auditoria`.
