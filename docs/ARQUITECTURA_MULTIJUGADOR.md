# Arquitectura multijugador: Arena Civitas (rúbrica §13, PDF pp. 9–10)

## Resumen

Es un multijugador **local cliente-servidor por sockets TCP** para **2 a 4 jugadores reales**, cada uno en su propio equipo y con un rol distinto. El **servidor es autoritativo**:
- mantiene la partida;
- controla el reloj;
- valida cada decisión;
- calcula la propagación, los indicadores, las puntuaciones y la elección.

Los clientes solo envían lo que el jugador eligió. No hace falta internet: funciona en la red del salón, sin Render ni Neon. La clasificación online del modo historia es un añadido aparte y **no** es este multijugador.

```
                           SERVIDOR  (clases/arena/servidor.py)
                 Partida (reglas.py): árbol + grafo + indicadores + elección
                                     |  TCP 50777, JSON por línea
          ┌──────────────────┬───────┴──────────┬──────────────────┐
      CLIENTE 1          CLIENTE 2          CLIENTE 3          CLIENTE 4
      Ciudadano          Periodista         Influencer         Candidato
   (Ren'Py, equipo A) (Ren'Py, equipo B) (Ren'Py, equipo C) (Ren'Py o bot)
```

El equipo que pulsa «Crear sala» ejecuta el servidor dentro del juego, en un hilo, y además su propio cliente. También existe un servidor dedicado sin interfaz: `python servidor_arena.py`.

## Capas

| Capa | Archivo | Depende de |
|---|---|---|
| Reglas (Python puro, sin red ni pantallas) | `game/clases/arena/reglas.py` | `Tree.py`, `GrafoSocial.py` |
| Protocolo (formato y validación) | `game/clases/arena/protocolo.py` | — |
| Transporte del servidor (sockets, hilos, reloj) | `game/clases/arena/servidor.py` | reglas, protocolo |
| Cliente (socket + cola) | `game/clases/arena/cliente.py` | protocolo |
| Interfaz | `game/arena/arena.rpy` | cliente (y servidor al crear sala) |
| Jugador automático | `game/clases/arena/bot.py`, `tests/arena_bot.py` | cliente |

Gracias a esta separación, las reglas se prueban sin Ren'Py (`tests/test_arena_motor.py`) y la red con clientes reales (`tests/test_arena_red.py`).

## Qué mantiene y sincroniza el servidor (lista del PDF)

| PDF | Dónde | Cómo llega a los clientes |
|---|---|---|
| Estado de la partida | `Partida.fase`, `ronda`, `indicadores` | mensaje `estado`, tras cada cambio |
| Jugadores | `Partida.jugadores` (rol, puntos, reputación, logros, conexión) | `estado.jugadores` |
| Publicaciones | `Partida.publicacion` (la verdad se oculta hasta el resultado) | `ronda.publicacion` y luego `resultado.publicacion` |
| Relaciones | `Partida.grafo` (grafo social con las cuentas de los jugadores) | `bienvenida.grafo` y `grafo` al empezar |
| Eventos | evento aleatorio de la ronda (con semilla) | `ronda.evento` |
| Puntuaciones | `Jugador.puntos` y `reputacion` (solo los calcula el servidor) | `estado`, `resultado.acciones`, `final.ranking` |
| Turnos | rondas simultáneas con límite de tiempo, pausa y continuar | `ronda.segundos`, `estado.restante`, `estado.decidieron` |
| Información compartida | resultado de propagación (alcanzados, protegidos, padres, saltos) | `resultado` |

## Protocolo (versión 1)

Un objeto JSON por línea (`\n`), UTF-8 y como máximo 16 KB. Todo mensaje lleva `v` (versión) y `tipo`.

**Cliente → servidor.** Todos llevan `id`, único por mensaje:

| tipo | campos | regla |
|---|---|---|
| `hola` | `nombre`, `rol`, `token?`, `clave?` | Une a la sala. Con `token` reconecta al mismo puesto. Con `clave` (la conoce solo quien creó la sala) queda como anfitrión. |
| `listo` | `listo` (bool) | — |
| `empezar` | — | Solo el anfitrión. Exige de 2 a 4 jugadores y que los demás estén listos. |
| `accion` | `ronda` (int), `ruta` (lista de int) | Ruta en el árbol del jugador. Debe ser de la ronda actual, terminar en una hoja y ser la primera de la ronda. |
| `pausa` | `pausar` (bool) | Solo el anfitrión. Congela el reloj del servidor. |
| `continuar` | — | Solo el anfitrión. Pasa a la siguiente ronda. |
| `salir`, `ping` | — | — |

**Servidor → cliente:**
- `bienvenida` lleva `jugador_id`, `token`, `anfitrion` y `grafo`.
- `estado` y `grafo` llevan lo que indica su nombre.
- `ronda` lleva `arbol` (el de ese jugador), `publicacion`, `evento` y `segundos`.
- `resultado` y `final` llevan lo que indica su nombre.
- `ack` y `error` llevan `codigo`, `mensaje` y `ref`.
- `cierre` avisa del fin de la sesión.
- Todo lo difundido lleva **`seq`** creciente: el cliente descarta lo que llegue repetido o fuera de orden.

## Robustez

- **Idempotencia:** el servidor recuerda los `id` de cada jugador. Un reenvío tras un corte recibe `ack` con `repetido: true` y no se aplica dos veces.
- **Carreras:** un único `RLock` protege la partida. Las acciones simultáneas se aplican en orden de llegada, pero se **resuelven** juntas y en orden fijo de jugador, así que el resultado es determinista.
- **Validación estricta:**
  - se descartan los campos desconocidos, como `puntos` o `indicadores` enviados por un cliente tramposo;
  - se rechazan los tipos incorrectos, incluido `true` como número;
  - tras 5 mensajes malformados se cierra esa sesión, y el servidor sigue atendiendo.
- **Tiempo:** el servidor fija el límite de cada ronda. Si se agota, quien no decidió cuenta como «sin respuesta», que resta participación.
- **Desconexión:**
  - en el lobby se libera el puesto y el rol;
  - en juego, el puesto se conserva (`conectado: false`) y la ronda no se bloquea esperándolo;
  - con su `token` vuelve al mismo puesto y recibe la ronda en curso.
- **Cierre ordenado:** `detener()` envía `cierre` a todos antes de cerrar los sockets.
- **Seguridad:** el cliente nunca calcula puntos. La verdad de la publicación no viaja hasta el resultado, y la fuente real solo va en el árbol del periodista.

## Por qué TCP y no otra cosa

- **TCP:** el PDF pide sockets. TCP garantiza el orden y la entrega, que es lo que importa en un juego por turnos de pocos jugadores.
- **JSON por línea:** se puede leer en la sustentación y depurar con `telnet`.
- **Navegadores:** no abren sockets TCP. Por eso la versión web **no** incluye la Arena y muestra un aviso para usar la de escritorio. Llevarla al navegador exigiría un adaptador WebSocket, que **no** está hecho.

## Cómo probarlo

```bash
python -m pytest -q tests/test_arena_red.py
python tests/qa_visual.py arena --salida <carpeta>
```

**`pytest`** cubre 12 pruebas:
- 2, 3 y 4 clientes en hilos y en **procesos independientes**;
- acciones simultáneas, tiempo agotado, pausa, ids repetidos y puntos falsos;
- mensajes malformados, reconexión con token, anfitrión por clave, roles duplicados y sala llena.

**`qa_visual.py arena`** lanza 4 procesos (2 Ren'Py con interfaz y 2 bots), juega la partida entera y guarda capturas de cada fase. Los 4 llegan al mismo resultado.

**En una LAN real** (no se ha podido probar aquí con varios PCs):
1. Ejecuta el juego de escritorio en el equipo anfitrión y elige «Arena (2-4 jugadores)» → «Crear sala». Permite el acceso cuando lo pregunte el firewall de Windows.
2. En los demás equipos, elige «Unirse» y escribe la IP que muestra la sala.

## Arena Online (mejora para la feria, no sustituye a la Arena local)

**Objetivo:** jugar desde teléfonos o computadores en redes distintas, sin instalar nada.

```
 Teléfono / PC (navegador)                      Render: civitas-leaderboard (FastAPI, 1 proceso)
 leaderboard/app/static/arena.html  ──HTTPS──▶  app/arena_online.py  (rutas /api/arena/…)
   (página ligera: dibuja y envía                     │ salas en memoria: {código → SalaArena}
    la ruta elegida del árbol)                        ▼
                                                game/clases/arena/sala.py  (sala: tokens, anfitrión,
                                                     │                      reloj, presencia, bots)
                                                     ▼
                                                game/clases/arena/reglas.py  ← el MISMO motor que la LAN
```

- **Un solo motor de reglas.** `SalaArena` envuelve la misma `Partida` de `reglas.py` que usa el servidor TCP. Árbol, grafo, propagación, puntos y elección son idénticos en local y online.
- **Transporte:** HTTPS con consultas periódicas, cada teléfono pide `GET /api/arena/salas/{código}` una vez por segundo. Se eligió frente a WebSocket por estas razones:
  - funciona detrás de cualquier proxy o wifi de feria;
  - no necesita conexiones persistentes en el plan gratuito de Render;
  - 1 s de latencia sobra para rondas de 25 s.
- **Reloj perezoso:** cada petición ejecuta `tick()`. El servidor sigue siendo autoritativo con los tiempos, sin hilos extra.
- **Servidor autoritativo:**
  - el cliente solo envía `{token, ronda, ruta, id}`;
  - la ruta se valida contra el árbol de ese jugador (`Partida.registrar_accion`);
  - los campos extra, como `puntos`, se ignoran;
  - el `id` de mensaje evita duplicados;
  - los tokens son secretos de 24 caracteres (`secrets.token_urlsafe`);
  - un token ajeno recibe 403.
- **Presencia y reconexión:** quien no consulta en 20 s queda «desconectado» y su ronda no bloquea a los demás. La página guarda su token en `localStorage` y, al reabrir el enlace, vuelve a su puesto.
- **Jugadores automáticos:** «Completar con jugadores automáticos» añade bots con la misma lógica que en la LAN (`bot.elegir_ruta`).
- **Límites:**
  - 300 salas como máximo, y cada una caduca tras 2 h sin actividad;
  - limitadores propios (`arena_get` 6000/min, `arena_accion` 1200/min y `arena_crear` 120/h por IP), separados de los del leaderboard;
  - cuerpo máximo de petición, el mismo del backend.
- **Leaderboard intacto:** las salas no usan la base de datos y las 142 pruebas del leaderboard siguen pasando.
- **Limitaciones del plan gratuito de Render:**
  - **Arranque en frío:** el servicio se duerme tras 15 min sin uso, y la primera visita tarda unos 50 s.
  - **Una instancia:** las salas viven en su memoria y se pierden si se reinicia. En la feria basta con abrir la página unos minutos antes. Para escalar habría que guardar las salas en Redis o en la base de datos, y no está hecho.
- **Lenguajes:** el núcleo, es decir las reglas, la sala y el servidor, es Python. La página `arena.html` es HTML/JavaScript **auxiliar**: solo dibuja y envía decisiones, sin lógica de juego. La entrega académica evaluable de §13 es la Arena local en Python/Ren'Py.

**Pruebas:**
- `cd leaderboard && python -m pytest -q tests/test_arena_online.py` (11 pruebas): partidas con 2, 3 y 4 jugadores; roles únicos, sala llena y código inexistente; anfitrión y «listo»; bots; token falso y puntos falsos; ruta inválida, otra ronda e idempotencia; tiempo agotado y desconexión; pausa; página servida.
- **Navegador (2026-11-08, local):** dos clientes en orígenes distintos (`localhost` y `127.0.0.1`) con viewport de móvil 375×812. Se probaron la creación, la unión con código, «listo», el inicio, la ronda con pista al verificar, el resultado sincronizado, la recarga con reconexión, las 5 rondas, la misma elección en ambos y el mensaje de sala inexistente. No hubo errores de consola ni del servidor.
- **Pendiente:** dispositivos físicos y despliegue en Render (`docs/PRUEBAS_FISICAS.md` §B).
