# Matriz de cumplimiento: rúbrica «LABORATORIO — ALCALDE DIGITAL»

- **Fuente:** `LABORATORIO 1 202630 (1).pdf` (15 páginas), leída completa.
- **Estado del código:** rama `feature/plataformero-arena-narrativa`, 2026-11-10.

**Estados:**
- **Probado:** cumple y fue probado.
- **Sin probar:** implementado pero no probado.
- **Parcial:** cumple parcialmente.
- **No cumple.**
- **Física:** requiere prueba física.

**Comandos de evidencia:**

| Clave | Comando | Resultado |
|---|---|---|
| [T] | `python -m pytest -q tests` | 180 pruebas |
| [B] | `cd leaderboard && python -m pytest -q` | 165 pruebas |
| [R] | `python tests/qa_recorridos.py` | 10/10: los 5 finales en historia y en feria |
| [V] | `python tests/qa_visual.py galeria …` y `… arena …` | Capturas reales del motor |
| [L] | `renpy.exe . lint` | Sin errores |

| § / pág. | Requisito | Archivo · clase/función | Prueba | Evidencia | Problema detectado | Corrección | Estado final |
|---|---|---|---|---|---|---|---|
| 1 / p.1 | Juego educativo, solo Java o Python | Ren'Py 8.5 (Python 3.12); `game/clases/*.py`; backend FastAPI | [T][B] | Repositorio | La página de la Arena Online es HTML/JS | Documentada como auxiliar (sin lógica de juego); la Arena evaluada es la local en Python | Probado |
| 2 / p.2 | Indicadores a subir y a bajar | Historia: `Ciudad.py`; Arena: `reglas.INDICADORES` | [T] `test_responsables_ganan…` | Capturas de la cabecera | — | — | Probado |
| 2 / p.2 | Sin preguntas de conocimiento; aprender por consecuencias | `publicaciones_historia.py`, `reglas._valorar` | [T] `test_coherencia_educativa.py` (12) | — | **En la historia, reportar noticias verdaderas y avalar rumores falsos daba puntos**, y «Verificar» no mostraba ninguna pista | Ramas equivocadas con coste; pista visible al verificar; la mejor acción coincide con la verdad en los 10 casos | Probado |
| 3 / p.2 | Ciudad Nova, cuatro candidatos, Civitas | Arena: `reglas.CANDIDATOS`; historia: `Eleccion.CANDIDATOS_HISTORIA` y línea del tarjetón en `domingo_tomas` | [T] `test_eleccion_historia.py`, [R] | Capturas `f0X_escrutinio_*` | La historia no mostraba cuatro candidatos; choque de nombres («Lucía», hija de Rodrigo, y la candidata «Lucía Prado») | Tarjetón y escrutinio con 4 candidatos; candidata renombrada a Inés Prado | Probado |
| 3 / p.2 | Publicaciones verdaderas, opiniones y falsas; compartir, verificar, ignorar o reportar | `reglas.PUBLICACIONES`, `arbol_base`; teléfono de la historia | [T] | Capturas de la ronda | Igual que §2 | Igual que §2 | Probado |
| 4 / p.3 | 2–4 jugadores, 4 roles con habilidades distintas | `reglas.ROLES`, `arbol_para`, `_conectar_jugador`, `_valorar` | [T] red y motor; [B] online | Capturas de sala y ronda | — | — | Probado (localhost) · Física (LAN) |
| 5 / pp.3–4 | Árbol n-ario: insertar, eliminar, buscar, recorrer, validar rutas, cambios por rol | `Tree.py` `ArbolDecisiones`; `reglas.arbol_para` | [T] `TestArbol` | `docs/ESTRUCTURAS_DATOS.md` | — | — | Probado |
| 5 / p.4 | AVL de publicaciones con balanceo | `ArbolAVL.py`, `Publicacion.BancoPublicaciones` | [T] `test_avl.py` (4) | — | **El AVL no tenía ninguna prueba** | Balance tras 100 inserciones ordenadas y 120 borrados; búsqueda; el banco entrega en orden de riesgo | Probado |
| 6 / p.5 | Grafo de la ciudad y grafo social (vértices, aristas, pesos) | `reglas.construir_grafo_ciudad/social`, `GrafoSocial` | [T] `TestGrafos` | — | — | — | Probado |
| 6 / p.5 | Operaciones: agregar y quitar vértices y aristas, BFS, DFS, BFS multifuente | `GrafoSocial.*` | [T] | — | — | — | Probado |
| 7 / p.6 | Propagación: quién, cuántos, velocidad, veracidad, consecuencias; decisiones distintas dan resultados distintos | `Partida.resolver_ronda` | [T] `test_reportes_frenan…` | Capturas `*_resultado`; partida online | — | — | Probado |
| 8 / pp.6–7 | 7 eventos aleatorios con semilla; la habilidad cuenta | `reglas.EVENTOS`; minijuegos | [T] `test_misma_semilla…` | — | — | — | Probado |
| 9 / p.7 | Tiempo limitado | Servidor TCP, `SalaArena.tick`, minijuegos | [T] `test_tiempo_agotado…`; [B] | Reloj en las capturas | — | — | Probado |
| 10 / pp.7–8 | Indicadores que cambian durante la partida | Arena y HUD de la historia | [T] | Capturas | — | — | Probado |
| 11 / pp.8–9 | Puntuación individual y resultado de la ciudad, logros, retroalimentación | `Jugador`, `_valorar`, `_logros`, `resultado_ciudad`; Puntuación Cívica | [T] | Capturas finales | Igual que §2 en la historia | Corregido | Probado |
| 12 / p.9 | Elección final ligada al comportamiento | Arena: `elegir_alcalde`; historia: `Eleccion.escrutinio_historia` + pantalla `escrutinio_historia` | [T] `test_rumores_cambian_el_ganador`, `test_las_decisiones_cambian_participacion_y_ganador` | Capturas | La historia no tenía recuento de votos | Escrutinio coherente con cada final, con explicación causal | Probado |
| 13 / pp.9–10 | Multijugador local cliente-servidor por sockets; el servidor sincroniza estado, jugadores, publicaciones, relaciones, eventos, puntos, turnos e información compartida | `clases/arena/servidor.py`, `cliente.py`, `protocolo.py`; `servidor_arena.py` | [T] `test_arena_red.py` (13): 2/3/4 en hilos y en procesos, simultaneidad, tiempo, pausa, duplicados, malformados, reconexión, anfitrión, **cierre** | [V] 2 Ren'Py + 2 bots | El cierre del servidor se mostraba como «se perdió la conexión» | Se conserva el motivo que envía el servidor (con prueba) | Probado (localhost, procesos independientes) · Física (varios PCs) |
| 13 (extra) | Torneo de la Arena: Consejo Cívico + 5 minijuegos como pruebas, puntuados por el servidor, con consecuencias sobre los indicadores compartidos | `clases/arena/torneo.py`, `servidor.py`, `arena/arena_torneo.rpy` | [T] `test_arena_torneo.py` (18): 2/3/4 jugadores en todas las fases, validadores, desconexión, duplicados, fuera de orden; [V] torneo Feria con 2 Ren'Py + 2 bots | `docs/ARENA_TORNEO.md`, `ARENA_MINIJUEGOS.md`, `ARENA_RITMO_MULTIJUGADOR.md` | El tiempo real de los minijuegos se mide en el cliente | Validación por rejuego o coherencia; documentado como limitación | Probado (localhost) · Física (partida humana completa) |
| 2 / p.2 (mejora) | Cinco retos con mecánicas distintas (sin arcades repetidos) | `clases/Plataformas.py`, `minijuegos/plataformas.rpy`; la Gran Viralización usa el plataformero | [T] `test_plataformas.py` (21), `test_plataformas_web.py`; [V] galería de minijuegos | `docs/PLATAFORMERO_RUTA_VERDAD.md`, `docs/auditoria/plat_*.jpg` | La Gran Viralización repetía el arcade de Caza-Rumores | Plataformero original con física determinista y rejuego en el servidor | Probado |
| 4 y 13 (extra) | Arena Online narrativa: historia compartida, cuatro perspectivas, cinco retos que juegan todos y decisión cívica tras cada uno | `clases/arena/campana.py`, `sala.py`, `caza_web.py`, `static/arena.html`, `*_motor.js` | [B] `test_arena_campana.py` (12); [T] `test_caza_web.py`, `test_plataformas_web.py`, `test_ritmo_web.py`; E2E con Chrome 2/3/4 | `docs/ARENA_NARRATIVA_MULTIPERSPECTIVA.md`, `docs/auditoria/online_*.jpg` | La Arena Online era una ronda de preguntas | Escenas con pista privada por rol; 5 retos jugables puntuados en el servidor; las pistas privadas no se filtran | Probado (local, Chrome) · Física (teléfonos) |
| 13 (extra) | Duelo de Frecuencias online (gran final de la Arena Online) | `static/ritmo_motor.js`, `clases/arena/duelo_online.py`, `sala.py` | [B] `test_arena_duelo_online.py` (10); [T] `test_ritmo_web.py` (equivalencia JS/Python); E2E con Chrome real 2/3/4 | `docs/ARENA_RITMO_MULTIJUGADOR.md` | Safari no reproduce OGG | Audio también en AAC | Probado (local, Chrome) · Física (teléfonos) |
| 13 (extra) | Arena Online 2–4 por navegador | `leaderboard/app/arena_online.py`, `clases/arena/sala.py`, `static/arena.html` | [B] `test_arena_online.py` (11); partida en el navegador con 2 clientes | `docs/ARQUITECTURA_MULTIJUGADOR.md` | — | — | Probado (local) · Sin probar en Render (falta el despliegue) |
| 14 / p.10 | Interfaz gráfica con todos los elementos | `arena.rpy`, `screens.rpy`, `arena.html` | [V] | Capturas a 1920, 1366, 1600×720 táctil y móvil 375×812 | — | — | Probado |
| 15 / pp.10–11 | Componente inclusivo y la dificultad que atiende | Avisos visuales de sonido (`sfx`), subtítulos, reducir movimiento, formas además de colores | [V] cliente con avisos | Captura «SONIDO ¡Logro!» | — | — | Probado |
| 16 / p.11 | AYUDA completa y mensajes en partida | `game/ayuda.rpy` (7 pestañas, incluida la Arena Online) | [V] | Capturas de ayuda | — | Añadida la sección online | Probado |
| 17 / pp.11–12 | Elementos motivadores funcionales | Logros, puntos, sonidos, animaciones | [V] | Capturas | Sin escucha humana | — | Probado (visual) · Física (audio) |
| 18 / pp.12–13 | Entrega final integrada y estable | Todo | [T][B][R][V][L] | — | — | — | Parcial: faltan las pruebas físicas |
| 19 / p.13 | Commits por integrante | Repositorio del equipo | `git log` | — | En `pruebaslaboratorio` solo hay commits de una cuenta | No se falsifica autoría: cada integrante sube su parte desde su cuenta | No verificable aquí |
| 20–21 / pp.13–15 | Sustentación y feria | `docs/GUIA_SUSTENTACION.md`, `docs/PLAN_DE_PRUEBAS_FERIA.md`, `docs/PRUEBAS_FISICAS.md` | — | — | — | — | Preparado |

**Bloqueantes académicos:** ninguno de implementación. Antes de entregar falta ejecutar `docs/PRUEBAS_FISICAS.md` (§A como mínimo) y que los commits del equipo estén en su repositorio.
