# Arena Civitas: torneo multijugador

**Flujo:** Lobby → Consejo Cívico → 5 pruebas con los minijuegos de la Historia → Elección → Resultados.

| Fase | Qué ocurre | Dónde está |
|---|---|---|
| Lobby | 2–4 jugadores, un rol cada uno. El anfitrión elige el modo: **Torneo completo**, **Torneo Feria** o **Solo Consejo** (la Arena anterior) | `arena/arena.rpy` (`arena_inicio`, `arena_sala`) |
| Consejo Cívico | Las rondas de siempre: árbol de decisiones por rol, propagación BFS por el grafo social, eventos con semilla e indicadores compartidos | `clases/arena/reglas.py` |
| Torneo | 5 pruebas en este orden: Moderación Express, Rastreador, Caza-Rumores, Ruta de la Verdad (plataformas) y **Duelo de Frecuencias como final** | `clases/arena/torneo.py`, `arena/arena_torneo.rpy` |
| Elección | `Partida.elegir_alcalde()` con los indicadores **después** del torneo (las pruebas cambian la ciudad) | `reglas.py` + `TorneoArena.final()` |
| Resultados | Dos conceptos distintos: **campeón del torneo** (puntos individuales) y **resultado de Ciudad Nova** (colectivo) | `arena_final_torneo` |

## Modos

| | Completo | Feria |
|---|---|---|
| Rondas del Consejo | 5 | 2 |
| Moderación (comentarios) | 12 (+2 si los conflictos ≥ 40) | 8 (+2) |
| Caza-Rumores | 40 s | 25 s |
| Ruta de la Verdad | nivel «arena» (80 s) | nivel «feria» (55 s) |
| Rastreador | 3 eslabones, 3 señuelos, 120 s | 2, 2, 75 s |
| Duelo | chart «historia», Normal | chart «feria», Normal |
| Duración aproximada | 25 min | 12 min |

La Feria no quita ninguna prueba: el árbol, el grafo, la propagación, los roles y los 5 minijuegos siguen presentes.

## Integración con el Consejo Cívico

Los indicadores **no se reinician**: cada prueba se prepara a partir de lo que dejó el Consejo, y su resultado colectivo vuelve a la ciudad.

**Del Consejo a la prueba** (`preparar_prueba`):
- **Moderación:** conflictos ≥ 40 → llegan 2 comentarios más.
- **Caza-Rumores:** desinformación ≥ 50 → el rumor arranca en 3 focos en vez de 2.
- **Ruta de la Verdad:** misma geometría y tiempo para todos; el Consejo solo cambia el relato (no la dificultad).
- **Rastreador y Duelo:** el contexto narrativo cita la partida.

**De la prueba a la ciudad** (`consecuencias`): la media del grupo (0–1) se centra en 0,5. Si el grupo juega bien, la ciudad mejora; si juega mal, empeora.

| Prueba | Indicadores afectados (máximo ±) |
|---|---|
| Moderación | convivencia ±6, confianza ±3 |
| Caza-Rumores | desinformación ∓8, rumores ∓4 |
| Rastreador | información verificada ±8, confianza ±3 |
| Ruta de la Verdad | conflictos ∓8, rumores ∓6 |
| Duelo | participación ±8, confianza ±3 |

La explicación de la elección añade una línea por cada prueba que cambió la ciudad.

## Puntuación

- **Cada prueba:** 0–1000 puntos, calculados **en el servidor** (ver `ARENA_MINIJUEGOS.md`).
- **Consejo Cívico:** `1000 + 1000·puntos / (20·rondas)`, acotado a 0–2000. 1000 equivale a un Consejo neutro.
- **Total máximo:** 2000 + 5 × 1000 = 7000.
  - El Consejo pesa un 29 %: más que cualquier prueba (14 %), pero no decide solo. Quien desinforma en el Consejo puede quedar por detrás aunque gane minijuegos, y al revés.
- **Desempate:** puntos del Duelo final y, después, orden de llegada.

## Servidor autoritativo

El servidor (`ServidorArena(torneo="completo"|"feria")`) controla todas las fases y difunde estos mensajes:
- `prueba`: misma spec para todos (semilla, ajustes, focos, chart y límite de tiempo).
- `mi_resultado`: solo al jugador que entregó.
- `resumen_prueba`: resultados de todos, cambios en la ciudad y clasificación.
- `final`: elección y torneo.

**Semilla de cada prueba:** `Random("torneo|<semilla de la partida>|<prueba>")`. Es reproducible y no depende de quién juega.

**El cliente envía sus decisiones, nunca sus puntos:** mensaje `resultado_prueba {indice, datos}`.

**Robustez:**

| Caso | Comportamiento | Prueba |
|---|---|---|
| Resultado duplicado (mismo `id`) | Se ignora (idempotencia del protocolo) | `test_resultado_fuera_de_orden_y_duplicado` |
| Segunda entrega con otro `id` | Rechazada: «Ya entregaste esta prueba» | `test_entrega_duplicada_y_jugador_desconocido` |
| Resultado de otra prueba (fuera de orden) | Rechazado: «Ese resultado es de otra prueba» | `test_resultado_fuera_de_orden_y_duplicado` |
| Datos imposibles (chart distinto, tiempo mayor que el límite, «contenido» con viralidad 100 %) | Rechazados con `ResultadoInvalido` | `TestPuntuacion` |
| Desconexión durante una prueba | No bloquea: si los conectados ya entregaron, se cierra; el ausente recibe 0 | `test_desconexion_durante_una_prueba` |
| Un cliente que nunca termina | Al vencer `limite_segundos(spec)` la prueba se cierra y recibe 0 | `limite_segundos` |
| Reconexión | El servidor reenvía la prueba en curso (`ya_entregaste`) o el último resumen; los pendientes se reenvían con el mismo `id` | `_reenviar_ronda` |

**Bots:** `BotArena` y `tests/arena_bot.py` entregan **decisiones** plausibles (`payload_bot`), que el servidor puntúa igual que las de una persona.

## Pruebas

| Comando | Qué cubre |
|---|---|
| `python -m pytest -q tests/test_arena_torneo.py` | 18 pruebas: puntuación y validadores de las 5 pruebas, peso del Consejo, reproducibilidad, campeón frente a ciudad, consecuencias, Feria y servidor TCP real con 2, 3 y 4 jugadores en todas las fases, desconexión, fuera de orden y duplicados |
| `python tests/qa_visual.py arena --tam 1920x1080 --salida <dir>` | 2 procesos Ren'Py + 2 bots por procesos. Torneo Feria completo con capturas de cada prueba, cada resumen y el final |

## Limitaciones conocidas (honestas)

- **Tiempo real medido en el cliente:** el servidor rejuega las decisiones (Moderación, Rastreador) y la carrera completa de la Ruta de la Verdad a partir de la traza de entradas, valida la coherencia (Caza-Rumores en Ren'Py) y recalcula el Duelo nota a nota. Sin embargo, el **momento** de cada pulsación lo mide el equipo del jugador. Un cliente modificado podría declarar mejores juicios de ritmo o una viralidad menor. Para un laboratorio en LAN se considera aceptable.
- **Arena Online:** juega los cinco retos en el navegador dentro de una historia compartida (ver `ARENA_NARRATIVA_MULTIPERSPECTIVA.md`).
- **QA automática:** en la QA, los clientes Ren'Py entregan decisiones de bot. Los minijuegos con ajustes de torneo son los mismos labels que usa la Historia, pero falta jugar a mano una partida completa del torneo: ver `docs/PRUEBAS_FISICAS.md`.
