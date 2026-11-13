# Plan de pruebas y contingencia: VI Feria Gamer (26-11-2026)

Lo que dice **PENDIENTE** no se ha probado: hay que hacerlo antes de la feria con el equipo real.

## 1. Montaje del stand (checklist)

- [ ] **Equipos:** 2–4 PCs con Windows y la versión de **escritorio** del juego (la Arena no funciona en el navegador).
- [ ] **Red:** un router propio o un punto de acceso del celular del equipo. **No depender del wifi del evento**, que suele aislar a los clientes entre sí.
- [ ] **Firewall:** en el PC anfitrión, abrir el juego una vez y aceptar el aviso del firewall de Windows (redes privadas). Puerto TCP **50777**.
- [ ] **Prueba de conexión:** «Crear sala» en el PC 1; en el PC 2, «Unirse» con la IP que muestra la sala. **PENDIENTE DE PRUEBA FÍSICA.**
- [ ] **Servidor dedicado opcional:** `python servidor_arena.py --rondas 3 --segundos 20` en un portátil con Python 3, para partidas más cortas en la feria.
- [ ] **Hardware:** cargadores y regletas, auriculares por puesto y volumen al 70 %.
- [ ] **Mando:** probar con el mando físico la historia (decisiones, minijuegos, pausa del duelo) y la Arena (opciones con cruceta + A). **PENDIENTE DE PRUEBA FÍSICA.**
- [ ] **Web y QR:** el QR de la pantalla final abre `https://ac020907.github.io/pruebaslaboratorio/` en un teléfono real. **PENDIENTE DE PRUEBA FÍSICA.**
- [ ] **Accesibilidad:** activar «Avisos visuales de sonido» en Opciones → Accesibilidad en los puestos con mucho ruido.

## 2. Pruebas antes del evento

| # | Prueba | Cómo | Resultado esperado | Estado |
|---|---|---|---|---|
| 1 | Suites automáticas | `python -m pytest -q tests` y `cd leaderboard && python -m pytest -q` | 110 y 142 OK | Verificado 2026-11-07 |
| 2 | Lint | `renpy.exe . lint` | Sin errores | Verificado |
| 3 | Arena con 4 procesos en un PC | `python tests/qa_visual.py arena --salida demo` | Los 4 llegan a la misma elección | Verificado |
| 4 | Arena en LAN con 2, 3 y 4 PCs | Crear y unirse; jugar 5 rondas | Mismo resultado en todas las pantallas | **PENDIENTE** |
| 5 | Desconectar el cable de un cliente a mitad de ronda y volver a conectarlo | Pulsar «Reconectar» en la pantalla «Conexión perdida» | La ronda no se bloquea; el jugador vuelve a su mismo puesto | Probado sin interfaz (`test_desconexion_y_reconexion_con_token`); con cable real **PENDIENTE** |
| 6 | Historia y feria completas | `python tests/qa_recorridos.py` | 5 finales en los dos modos | Verificado |
| 7 | Partida de feria cronometrada con personas | Cronómetro | 9–13 min | **PENDIENTE** |
| 8 | Arena con personas | 2–4 visitantes, 5 rondas | 4–6 min, sin explicación del equipo | **PENDIENTE** |
| 9 | Escucha de voces, música y duelo | Auriculares | Sin cortes ni volumen excesivo | **PENDIENTE** |

## 3. Contingencias

| Problema | Plan B |
|---|---|
| Los PCs no se ven en la red (aislamiento del wifi) | Router o punto de acceso propio. Si tampoco, un solo PC con «Añadir jugador automático» y los visitantes por turnos. |
| El firewall bloquea el puerto | Permitir el juego en redes privadas, o usar `servidor_arena.py` en un equipo ya configurado. |
| El anfitrión se cuelga | Cerrar y «Crear sala» de nuevo (la partida dura 5 minutos). Los demás vuelven a «Unirse». |
| Sin internet | La historia y la Arena funcionan offline. La clasificación guarda el resultado y lo envía en la siguiente partida. |
| Sin audio o mucho ruido | Avisos visuales de sonido; todo el diálogo está escrito. |
| Falla un mando | Teclado: Enter acepta y las flechas eligen. |
| Teléfono sin horario | Mostrar el QR desde el PC; la web carga en cualquier teléfono en horizontal. |
| Algo grave a última hora | Demo grabada o las capturas de `docs/auditoria` y la guía `docs/GUIA_SUSTENTACION.md`. |

## 4. Limitaciones conocidas (para no prometer de más)

- La Arena no está en la versión web: los navegadores no abren sockets TCP.
- En el lobby, quien se desconecta libera su puesto y vuelve a unirse como nuevo. En juego conserva el puesto y vuelve con «Reconectar». Si se cae el anfitrión (el servidor), la partida termina.
- Los avisos visuales salen para los sonidos de juego que pasan por `sfx()` (pista, logro, error, alarma, notificación, decisión), no para la música ni las voces. Las voces ya tienen subtítulos.
