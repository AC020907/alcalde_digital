# Estructuras de datos: árboles y grafos en Civitas

Este documento corresponde a la rúbrica §5–7 (PDF, pp. 3–6). El código citado existe y está probado. Las pruebas se ejecutan con estos comandos:

```bash
python -m pytest -q tests/test_arena_motor.py
python -m pytest -q tests/test_civitas_logica.py
```

## 1. Árbol de decisiones de cada publicación

**Código:**
- `game/clases/Tree.py` (`ArbolDecisiones`) y `game/clases/Node.py` (`NodoDecision`).
- **Árbol de la Arena:** `game/clases/arena/reglas.py`, funciones `arbol_base()` y `arbol_para(rol, pub, candidato)`.
- **Historia:** `game/clases/Publicacion.py` (`armar_publicacion`), que se usa en el teléfono de Civitas.

```
                ¿Qué quieres hacer?                (raíz)
      /            |              \          \
  Compartir    ¿Es verdadera?      Ignorar    Reportar      [+ Responder con datos, solo el candidato]
               /          \
  Sí: compartir con fuente   No: reportarla
```

### Las cinco preguntas del PDF (p. 4)

1. **¿Qué problema resuelve?**
   - Cada publicación ofrece un conjunto de acciones posibles. Algunas dependen de una decisión anterior: solo se compara la fuente si antes eliges verificar.
   - El árbol representa ese flujo, y la hoja a la que llega el jugador es la **consecuencia** que el servidor aplica.
   - Además, el árbol **cambia según el rol**, sin escribir un flujo distinto para cada caso.
2. **¿Por qué un árbol?**
   - Las decisiones son jerárquicas y no tienen ciclos: de cada pregunta salen opciones, y ninguna vuelve atrás.
   - Una ruta raíz → hoja es exactamente lo que hizo el jugador. Viaja por la red como lista de índices, por ejemplo `[1, 1]` = Verificar → No.
   - El servidor la valida recorriendo el árbol, sin confiar en lo que diga el cliente.
3. **¿Qué variante?** Un **árbol general (n-ario)**, porque un nodo puede tener 2, 4 o 5 hijos. Cada nodo guarda `texto`, `consecuencia`, `etiqueta`, `hijos` y `padre`.
   - **El AVL de la historia:** la historia usa además un **AVL** (`game/clases/ArbolAVL.py`). Ahí está el banco de publicaciones ordenado por nivel de riesgo (`BancoPublicaciones`): `siguiente()` saca el mínimo en O(log n) y lo elimina con rotaciones.
4. **¿Cómo se insertan y eliminan elementos?**
   - **Inserción:** `insertar_raiz(texto)` crea la raíz. `insertar_hijo(padre, texto, consecuencia, etiqueta)` añade una opción y enlaza `hijo.padre`, en O(1).
   - **Eliminación:** `eliminar(nodo)` quita el nodo con todo su subárbol desde su padre, en O(k) con k = número de hijos del padre.
   - **Uso real en el juego:** si la publicación habla de la candidatura del jugador Candidato, `arbol_para` **elimina** la rama *Reportar*, porque no puede censurar críticas propias por conflicto de interés. En su lugar **inserta** *Responder con datos*.
   - **Búsqueda previa:** `buscar(etiqueta)` localiza el nodo antes de eliminarlo (DFS en preorden, O(n)).
5. **¿Cómo se recorre?**
   - **Preorden** (`preorden`) y **posorden** (`posorden`) son recursivos; **por niveles** (`recorrido_por_niveles`) usa BFS con cola.
   - `recorrer_ruta(indices)` sigue la ruta del jugador y devuelve `None` si es inválida (índice fuera de rango o un booleano).
   - `hojas()` devuelve las consecuencias posibles. `altura()` da 3 y `tamanio()` da 7 en el árbol base.
   - **Recorrido para enviar el árbol:** el cliente recibe el árbol serializado mediante un preorden recursivo (`arbol_a_dict`).

**Pruebas** (`TestArbol`):
- **`test_arbol_del_pdf`:** el recorrido por niveles coincide con el PDF; altura 3, 7 nodos y 5 hojas.
- **`test_insertar_buscar_eliminar_y_recorrer`:** preorden y posorden; eliminación de un subárbol; rutas inválidas.
- **`test_candidato_no_reporta_lo_suyo_y_puede_responder`.**
- **`test_periodista_ve_la_fuente_y_los_demas_una_pista`.**

## 1b. AVL del banco de publicaciones (modo Historia)

`game/clases/ArbolAVL.py`, usado en `Publicacion.BancoPublicaciones`.

- **Clave:** el nivel de riesgo de la publicación.
- **Uso en el juego:** el teléfono entrega las publicaciones de menor a mayor riesgo. `siguiente()` toma el mínimo y lo borra, en O(log n).
- **Balanceo:** el factor de equilibrio se mantiene en [-1, 1] mediante rotaciones simples y dobles en `insertar` y `eliminar`.
- **Pruebas** (`tests/test_avl.py`):
  - 100 inserciones **en orden**, el peor caso para un ABB sin balanceo: sigue balanceado y con altura ≤ 8;
  - 200 inserciones y 120 borrados aleatorios: se balancea tras cada borrado;
  - búsqueda, mínimo y máximo;
  - el banco real entrega las 10 publicaciones en orden de riesgo.

## 2. Grafo social (dirigido y ponderado)

**Código:** `game/clases/GrafoSocial.py`; la red de la Arena la construye `construir_grafo_social()`.

- **Vértices:** 16 ciudadanos. Incluye los del PDF (Ana, Luis, Pedro, Carlos, María), cada uno con su zona. Además, 4 cuentas de candidato, las cuentas que publican y **una cuenta por jugador**, que se añade al unirse y se elimina si sale del lobby.
- **Aristas `origen → destino`:** "lo que publica origen le llega a destino" (seguimiento). El **peso** (0–1) es la fuerza de esa conexión, es decir, la probabilidad de que la publicación cruce.
- **Por qué dirigido:** seguir a alguien no es recíproco. El influencer llega a muchos, pero pocos le llegan a él.
- **Por qué ponderado:** no todas las relaciones pesan igual. Los ciclos existen, como Carlos ↔ María, y el BFS los maneja con `visitados`.
- **Representación:** listas de adyacencia salientes (`adyacencia`) y entrantes (`entrantes`), que permiten recorrer hacia atrás.

| Operación | Método | Complejidad |
|---|---|---|
| Agregar vértice / arista | `agregar_usuario`, `agregar_conexion` | O(1) |
| Eliminar arista | `eliminar_conexion` | O(1) |
| Eliminar vértice (con todas sus aristas) | `eliminar_usuario` | O(grado) |
| Adyacencia, predecesores, peso | `vecinos`, `predecesores`, `peso` | O(1) / O(grado) |
| BFS por niveles desde una fuente | `bfs_propagacion` | O(V + E) |
| **BFS multifuente** (todos los que comparten en la ronda) | `bfs_multifuente` | O(V + E) |
| DFS (cadena de difusión hacia atrás, en el Rastreador de la historia) | `dfs_buscar` | O(V + E) |

## 3. Grafo de la ciudad (no dirigido)

Es el grafo de la página 5 del PDF: `COLEGIO — BARRIO`, `BARRIO — PARQUE`, `BARRIO — PLAZA`, `PLAZA — ALCALDÍA`. Lo construye `construir_grafo_ciudad()`, con dos aristas por calle.

**Función en el juego:** `distancias_zona()` hace un BFS desde la zona de la publicación. Los ciudadanos de esa zona empiezan el boca a boca (distancia 0), y la pantalla resalta la zona y sus calles.

**Prueba:** las distancias desde Colegio son `{colegio: 0, barrio: 1, parque: 2, plaza: 2, alcaldia: 3}`.

## 4. Árbol → grafo → indicadores → puntuación → elección

Todo lo hace el servidor en `Partida.resolver_ronda()`, en un mismo turno:

1. **Hoja del árbol de cada jugador:**
   - *Compartir* y *Sí: compartir con fuente* convierten la cuenta del jugador en **fuente** del BFS. Su fuerza depende del rol: influencer ×2, candidato ×1,3.
   - *Reportar* y *No: reportarla* **bloquean** a quienes siguen al jugador. El ciudadano protege a toda su zona, y el desmentido del periodista protege su red hasta 2 saltos.
   - Con 2 reportes, Civitas **retira** la publicación: el autor apenas propaga.
2. **`bfs_multifuente`** calcula qué ciudadanos reciben la publicación, **cuántos**, en **cuántos saltos** (la velocidad) y quién se la pasó a quién (`padres`, que son las flechas verdes de la pantalla).
3. **Consecuencias según la verdad de la publicación:**
   - **Falsa:** desinformación, rumores, conflictos y menos confianza, proporcional al alcance (×0,4 si se desmintió).
   - **Verdadera:** información verificada, participación y confianza.
   - **Opinión:** conflictos o convivencia según cómo se compartió. Reportar opiniones también resta convivencia.
4. **Puntuación individual** (`_valorar`): una acción responsable suma y una irresponsable resta. El influencer pesa ×2, y hay bonos de periodista, ciudadano y candidato. Además se otorgan **logros**.
5. **Confianza de cada ciudadano alcanzado** en el candidato del que habla la publicación (`confianza_cand`). La **elección final** (`elegir_alcalde`) usa esa confianza más la reputación del jugador Candidato, y la **participación** decide la abstención.
   - **Explicación causal:** cada cambio queda registrado en `causas`, que es lo que muestra la pantalla "¿Por qué ganó?".

**Pruebas:**
- **`test_reportes_frenan_la_propagacion_del_rumor`:** jugar responsable da menos alcance y menos desinformación que jugar irresponsable, y cada nodo alcanzado tiene un padre conectado por una arista real.
- **`test_responsables_ganan_puntos_y_la_ciudad_mejora`.**
- **`test_rumores_cambian_el_ganador`:** desmentir un rumor contra Prado le da más confianza que compartirlo.
- **`test_participacion_cambia_la_abstencion`.**

## 4b. Estructuras de apoyo de la versión final

- **Ruta de la Verdad** (`clases/Plataformas.py`): el nivel es una **lista de segmentos** que se convierte en una **rejilla de tiles** (matriz); la partida guarda una **traza** (lista de entradas por tick) que el servidor vuelve a jugar para validar el puntaje.
- **Alias de expresiones** (`ALIAS_EXPRESION`): **diccionario** (personaje, expresión) → archivo real, para no duplicar imágenes idénticas.

## 5. Ejemplo reproducible

```bash
cd game
python -c "from clases.arena.reglas import *; g=construir_grafo_social(); print(g.bfs_multifuente(['ana'], semilla='demo'))"
```

La misma semilla da siempre la misma propagación (`test_misma_semilla_misma_propagacion`). Semillas distintas cambian las publicaciones y los eventos entre partidas (`test_misma_semilla_misma_partida_y_semillas_distintas_varian`).
