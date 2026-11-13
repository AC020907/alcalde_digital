# Bugfix: la Arena del escritorio volvía al menú al pulsar «Siguiente ronda»

## Problema

En el juego de escritorio (Ren'Py, Windows), al crear una sala, responder una publicación y pulsar «Siguiente ronda», la partida desaparecía y el juego volvía al menú principal. No había `traceback.txt` porque no se producía ninguna excepción. La versión web no tenía el problema: usa su propio cliente.

**Reproducción (2026-11-12, juego real con clics en la ventana):** Arena → nombre → «Crear sala en este equipo» → «Jugar con jugadores automáticos» → «Verificar» → «No: reportarla» → «Siguiente ronda» → menú principal.

## Causa raíz

- `game/clases/arena/cliente.py`, `ClienteArena.enviar()` (línea 91): devuelve el id del mensaje (`return mensaje["id"]`).
- Cuatro botones lo llamaban directamente con `action Function(c.enviar, ...)`:
  - `game/arena/arena.rpy`: «Estoy listo» (línea 500), «Pausar ronda» (576) y «Siguiente ronda» (631).
  - `game/arena/arena_torneo.rpy`: «Siguiente prueba / Ir al Duelo / Ver la elección» (185).
- En Ren'Py, cuando una acción `Function(f)` devuelve un valor distinto de `None`, la interacción termina con ese valor. `call screen arena_partida` devolvía el id; el bucle `while arena_seguir` del label `arena` lo tomaba como «salir», ejecutaba `arena_salir()` (cerrando el servidor y los bots) y volvía al menú.
- **Por qué no lo detectaban las pruebas:** la QA automática llamaba a `c.enviar("continuar")` desde Python, no como acción de un botón.

## Corrección

- Nueva función `arena_enviar(tipo, **datos)` en `game/arena/arena.rpy`: envía con `AS.cliente.enviar` y no devuelve nada.
- Los cuatro botones usan `Function(arena_enviar, ...)`.
- No cambian el protocolo, el servidor, `ClienteArena` ni la web.

## Archivos

| Archivo | Cambio |
|---|---|
| `game/arena/arena.rpy` | `arena_enviar` y 3 botones |
| `game/arena/arena_torneo.rpy` | 1 botón |
| `tests/test_arena_acciones_pantalla.py` | Nuevo: falla si un botón de la Arena llama directamente a un método del cliente que devuelve valor |
| `game/qa_galeria.rpy` | Nueva etapa `arena_solo_completa`: anfitrión solo con bots en el mismo proceso, partida completa |
| `docs/BUGFIX_ARENA_ONLINE_LOCAL.md` | Este informe |

## Pruebas

| Prueba | Resultado |
|---|---|
| `pytest tests/test_arena_acciones_pantalla.py` antes de la corrección | **2 fallos** (reproduce el defecto) |
| La misma prueba después | 2 OK |
| `python -m pytest -q tests` | **182 OK** (incluye `test_arena_red`: 2/3/4 jugadores, reconexión, desconexión, cierre del servidor, duplicados) |
| `renpy.exe . lint` | Sin errores |
| Juego real con clics (anfitrión + bots, Torneo Feria) | Responder → «Siguiente ronda» → ronda 2 → «Pausar/Reanudar» → Moderación Express jugada a mano → resultados → «Siguiente prueba» → Rastreador. Sin volver al menú |
| `qa_visual.py galeria --etapas arena_solo_completa` (modo completo) | OK: 5 rondas, 5 pruebas y final |
| Ídem, modo «Solo Consejo» | OK: 5 rondas y elección final |
| `qa_visual.py arena` (2 Ren'Py, anfitrión + cliente que se une, y 2 bots externos; Torneo Feria) | OK: los 4 terminan con el mismo resultado |

## Protección de la versión web

`git diff --name-status` solo muestra `game/arena/arena.rpy`, `game/arena/arena_torneo.rpy` y `game/qa_galeria.rpy`, además de la prueba y este documento, que son nuevos. Sin cambios en `leaderboard/` (backend, `static/arena.html`, motores JS), en GitHub Pages ni en Render. No se reconstruyó ni se publicó la web.

## Pendientes

- **Distribución desactualizada:** el zip de Windows ya publicado (`civitas-dist` y la release `v2.0-final` de `alcalde_digital`) tiene el defecto. Hay que regenerarlo y volver a subirlo.
- **Pruebas físicas:** anfitrión y clientes en PCs distintos de la misma LAN, con personas.
- **Rondas jugadas a mano:** solo se jugaron hasta Rastreador. El resto del torneo lo recorrió la QA automática, que entrega las pruebas con decisiones de bot.
