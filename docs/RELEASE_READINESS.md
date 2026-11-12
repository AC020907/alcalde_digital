# Release readiness: corrección de pendientes, Arena Online, torneo y validación final

## 0000. Release final: sprites oficiales y pulido (rama `release/final-sprites-pulido`; recuperación: tag `checkpoint-pre-release-final`)

| Comando (2026-11-11) | Resultado |
|---|---|
| `python -m pytest -q tests` | **180 OK** (43 subtests) |
| `cd leaderboard && python -m pytest -q` | **165 OK**. Una ejecución terminó con un volcado de hilos al cerrar el intérprete; al repetirla salió limpia |
| `renpy.exe . lint` | Sin errores |
| `python tests/qa_recorridos.py` | **10/10** finales en historia y feria |
| `qa_visual.py galeria --etapas personajes` | OK: 5 hojas de contacto, 30 expresiones en escena, dos personajes y retrato lateral |
| `qa_visual.py galeria --etapas minijuegos` | OK: incluye la pausa de Moderación y el plataformero (178 FPS, victoria y resultado) |
| `qa_visual.py galeria --etapas menus,ritmo,finales` | OK: Duelo con la NOVA nueva y los 5 escrutinios y finales |
| `qa_visual.py arena --tam 1920x1080` | OK: torneo LAN con 2 Ren'Py + 2 bots |
| `python tests/e2e_arena_online.py --jugadores 2,3,4` | **OK** (salida 0): salas de 2, 3 y 4 navegadores, 5 retos cada una, con campeón y escrutinio; NOVA nueva en el Duelo web. Servidor local, no Render |

**Qué cambió:** ver `docs/SPRITES.md` y `docs/PLATAFORMERO_RUTA_VERDAD.md` (presentación y consecuencias).

**Estado:**
- **Entrega académica: GO condicionado** a la prueba en LAN física (`docs/PRUEBAS_FISICAS.md` §A).
- **Feria: GO condicionado** a una partida Online con teléfonos y personas (§B) y al despliegue en Render.
- **Tomás:** sprites nuevos integrados (2026-11-11). Lint, 180 + 165 pruebas, 10/10 recorridos y galería de personajes OK.

## 000. Plataformero y Arena Online narrativa (rama `feature/plataformero-arena-narrativa`; recuperación: tag `checkpoint-pre-plataformero`)

**Qué cambió:**
- **La Gran Viralización** ya no repite el arcade de Caza-Rumores: su reto es el plataformero **Ruta de la Verdad**, en Historia, Feria y torneo LAN. Detalle en `docs/PLATAFORMERO_RUTA_VERDAD.md`.
- **La Arena Online** es una historia compartida de 5 rondas con cuatro perspectivas y pistas privadas. Los cinco retos se juegan en el navegador y todos compiten; después de cada reto vienen una decisión cívica y su consecuencia. Detalle en `docs/ARENA_NARRATIVA_MULTIPERSPECTIVA.md`.

| Comando (2026-11-10) | Resultado |
|---|---|
| `python -m pytest -q tests` | **179 OK** (43 subtests) |
| `cd leaderboard && python -m pytest -q` | **165 OK** |
| `renpy.exe . lint` | Sin errores |
| `python tests/qa_recorridos.py` | **10/10** finales en historia y feria |
| `python tests/qa_visual.py galeria --etapas minijuegos` | OK: plataformero en el motor real (tutorial, juego, resultado) |
| `python tests/qa_visual.py arena --tam 1920x1080` | OK: torneo LAN con 2 Ren'Py + 2 bots y las 5 pruebas (plataformas incluida, rejugada en el servidor) |
| `python tests/e2e_arena_online.py --jugadores 2,3,4` | OK: Chrome real (PC y móvil táctil), latencia de 0–350 ms, recarga a mitad de Caza-Rumores. Campaña completa (5 escenas, 5 retos, 5 decisiones) en unos 160 s con autojuego; final idéntica en todos los navegadores |

**Evidencias:** `docs/auditoria/online_*.jpg` y `plat_*.jpg`.

**Duración real:** no se midió con personas. El autojuego no lee las escenas: una partida Feria con humanos tardará más (lectura de hasta 40 s por escena). Hay que medirla en `docs/PRUEBAS_FISICAS.md`.

**Pendiente:**
- Probar en teléfonos reales y con personas.
- Merge a `main` y despliegue (requieren autorización).
- Manual Deploy en Render.

## 00. Duelo de Frecuencias en la Arena Online (rama `feature/arena-online-duelo`; recuperación: tag `checkpoint-pre-duelo-online`)

| Comando (2026-11-09) | Resultado |
|---|---|
| `python -m pytest -q tests` | **151 OK**, con 2 de equivalencia JS/Python (27 subtests: 30, 60 y 144 Hz, latencia simulada) |
| `cd leaderboard && python -m pytest -q` | **163 OK** (10 nuevas del duelo online) |
| `python tests/e2e_duelo_online.py --jugadores 2,3,4` | OK con Chrome real (PC y móvil táctil), latencia de 0 a 400 ms, recarga y desconexión a mitad de canción. Puntos del navegador iguales a los del servidor; final idéntica en todos |
| `renpy.exe . lint` | Sin errores |

Detalle en `docs/ARENA_RITMO_MULTIJUGADOR.md` §Online. Evidencias: `docs/auditoria/online_duelo_*.jpg`.

**Pendiente:** probar en teléfonos reales (iPhone/Safari y Android), con auriculares Bluetooth.

## 0. Torneo de la Arena (rama `feature/arena-torneo`; recuperación: tag `checkpoint-pre-torneo`)

| Comando (2026-11-08) | Resultado |
|---|---|
| `python -m pytest -q tests` | **149 OK** (131 anteriores + 18 del torneo) |
| `renpy.exe . lint` | Sin errores |
| `python tests/qa_recorridos.py` | **10/10**: los 5 finales en historia y en feria (regresión tras tocar Moderación, Rastreador y Duelo) |
| `python tests/qa_visual.py arena --tam 1920x1080` | OK: 2 Ren'Py + 2 bots por procesos. Torneo Feria de punta a punta (2 rondas, 5 pruebas, 5 resúmenes y final); ambos clientes con el mismo campeón y la misma elección |

**Qué es:** Consejo Cívico → 5 pruebas → elección. Detalle en `docs/ARENA_TORNEO.md`. QA también a 1366×768 (OK). Evidencias: `docs/auditoria/torneo_*.jpg`.

**Pendiente:**
- Una partida humana completa del torneo (los minijuegos los entregó un bot en la QA).
- Probar en LAN física.
- Conectar el torneo a la Arena Online: decisión pendiente, porque los minijuegos no corren en el navegador.


- **Rama:** `fix/rubrica-online`, que sale de `main` `d3c0a5b` (versión publicada el 2026-11-08). El punto de recuperación es el tag `checkpoint-pre-online`.
- **Fecha:** 2026-11-08. **SDK:** Ren'Py 8.5.3.
- **Estado:** commits locales en la rama. **Sin push, sin merge a `main`, sin despliegue:** requieren autorización.
- **Veredicto:**
  - **Entrega académica: GO condicionado**, a ejecutar `docs/PRUEBAS_FISICAS.md` §A (LAN real).
  - **Arena Online: lista para desplegar**, pendiente de autorización y de la prueba §B con teléfonos.

## 1. Problemas encontrados y corregidos

| Gravedad | Problema | Corrección | Prueba |
|---|---|---|---|
| Alta (educativo) | En la historia, reportar como falsa una noticia **verdadera** daba puntos y bajaba la desinformación (5 de 5 publicaciones verdaderas). Avalar un rumor **falso** («Sí, es verdad») también daba puntos (5 de 5 falsas). | Ramas equivocadas con coste en puntos, reputación e indicadores. Compartir algo falso sin verificar ahora resta puntos. | `tests/test_coherencia_educativa.py` (12) |
| Alta (educativo) | «Verificar» en el teléfono de la historia no mostraba ninguna evidencia: se decidía a ciegas | Cada publicación muestra una pista al verificar (`publicaciones_historia.py`) | Mismo archivo |
| Media | La historia no tenía cuatro candidatos ni recuento de votos (§3, §12) | Línea del tarjetón el domingo y pantalla de **escrutinio** coherente con cada final (`clases/Eleccion.py`) | `tests/test_eleccion_historia.py` (4); [R] 10/10 |
| Media | Choque de nombres: «Lucía» (hija de Rodrigo) y la candidata «Lucía Prado» | La candidata pasa a llamarse **Inés Prado** | — |
| Media | El AVL no tenía ninguna prueba | `tests/test_avl.py`: balanceo, borrado, búsqueda y orden de entrega | 4 pruebas |
| Baja | Al cerrarse el servidor LAN, el cliente decía «se perdió la conexión» en vez de «el servidor se cerró» | El cliente conserva el motivo que envía el servidor | `test_cierre_ordenado_del_servidor` |
| Baja | Documentación con rutas y repositorio antiguos (`alcalde_digital`) en los pasos de despliegue | Se distinguen el repositorio de desarrollo y despliegue (`pruebaslaboratorio`) y el académico (`alcalde_digital`) | — |

## 2. Funcionalidad nueva

**Arena Online (2–4 jugadores por navegador):**
- **Código:** `game/clases/arena/sala.py` (sala sobre el mismo `reglas.py`), `leaderboard/app/arena_online.py` (API HTTPS) y `leaderboard/app/static/arena.html` (página para móvil en `/arena`).
- **Acceso desde el juego:** en la web, el botón Arena abre la versión online; en escritorio hay un enlace en la Arena local.
- **AYUDA:** incluye una sección sobre la Arena Online.

## 3. Pruebas ejecutadas (2026-11-08)

| Comando | Resultado |
|---|---|
| `python -m pytest -q tests` | **131 OK** |
| `cd leaderboard && python -m pytest -q` | **153 OK** (142 del leaderboard + 11 de la Arena Online) |
| `renpy.exe . lint` | Sin errores |
| `python tests/qa_recorridos.py` | **10/10**: los 5 finales en historia y en feria, también con las consecuencias corregidas |
| `python tests/qa_visual.py arena --tam 1920x1080` y `--tam 1366x768` | OK en ambas: 4 procesos (2 Ren'Py + 2 bots), los 4 con la misma elección |
| `python tests/qa_visual.py galeria --etapas finales,menus` a 1920, 1366 y 1600×720 táctil | OK en las 3: menús, historial, 5 escrutinios y 5 pantallas de resultados |
| Arena Online en el navegador (local, 2 clientes, viewport 375×812) | Partida completa, misma elección en ambos, recarga con reconexión, sala inexistente con mensaje claro, sin errores de consola |

**Evidencias:** `docs/auditoria/historia_escrutinio_*.jpg`, `arena_1366_resultado.jpg` y `online_0*_*.jpg`.

## 4. Estado

| Área | Estado |
|---|---|
| Rúbrica (ver `docs/RUBRICA_CUMPLIMIENTO.md`) | Todos los requisitos implementados y probados. LAN con varios PCs y audio: requieren prueba física |
| Multijugador local (TCP) | Probado con procesos independientes en un PC (2, 3 y 4). **Sin probar en LAN física** |
| Multijugador online | Probado en local. **No desplegado** en Render; no probado con teléfonos reales |
| Historia | 5 finales alcanzables y escrutinio nuevo |
| Backend y leaderboard | 142 pruebas sin cambios de comportamiento; sin cambios de esquema |

## 5. Pendiente

**Antes de la entrega (16–20 nov):**
1. `docs/PRUEBAS_FISICAS.md` §A: LAN con 2, 3 y 4 PCs.
2. Commits de cada integrante en el repositorio académico.

**Antes de la feria (26 nov):**
1. Autorizar el merge y el **Manual Deploy** en Render (`DESPLIEGUE.md` §6).
2. §B (teléfonos) y §C (mando, audio y sesiones con personas).
3. Regenerar la web y el zip de Windows desde `main` para incluir estos cambios.

## 6. Rollback

- **Código:** `main` no se ha tocado: basta con no fusionar la rama. Si ya se fusionó, `git revert -m 1 <merge>`.
- **Backend:** la Arena Online solo añade rutas. Revertir el commit y redesplegar deja el leaderboard como estaba.
