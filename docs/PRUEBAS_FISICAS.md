# Pruebas físicas (equipos reales): protocolo para el equipo

Estas pruebas **no se pueden hacer desde un solo PC**. Cuatro procesos en `localhost` no equivalen a cuatro computadores en una red real, porque cambian el firewall, el wifi, la latencia y los cortes de red. Nada de lo que sigue está verificado hasta que el equipo lo ejecute y llene la columna «Resultado». No hace falta tocar código.

**Material:**
- 2 a 4 PCs con Windows y `DigitalMayor-2.0-win.zip` descomprimido.
- 2 a 4 teléfonos (Android e iPhone si es posible).
- Un router o punto de acceso propio.
- Un mando.
- Un cronómetro.

## A. Arena local (LAN, sockets TCP)

| # | Paso | Esperado | Resultado (fecha, quién, OK/fallo + nota) |
|---|---|---|---|
| A1 | PC1: Arena → Crear sala. Aceptar el firewall en **redes privadas**. | La sala muestra una IP 192.168.x.x y el puerto 50777 | |
| A2 | PC2: Arena → Unirse con esa IP, rol distinto → Estoy listo | En el PC1 aparece «Listo» | |
| A3 | PC1: Empezar (2 jugadores). Jugar 5 rondas | Las dos pantallas muestran el mismo resultado en cada ronda y la misma elección | |
| A4 | Repetir con 3 y luego 4 PCs | Igual que A3 | |
| A5 | PC2 intenta el mismo rol que el PC3 | Mensaje «Ese rol ya está ocupado» | |
| A6 | A mitad de una ronda, desconectar el wifi del PC3 durante 10 s y volver a conectarlo | La ronda no se bloquea. En el PC3 aparece «Conexión perdida» → **Reconectar** → vuelve a su puesto | |
| A7 | El anfitrión pulsa Pausar ronda y espera 20 s | El reloj se congela en todos los PCs y luego sigue | |
| A8 | Cerrar el juego del anfitrión en mitad de una partida | En los demás aparece «El servidor se cerró» | |
| A9 | El anfitrión solo: «Jugar con jugadores automáticos» | La partida empieza con 3 bots | |
| A10 | (Opcional) `python servidor_arena.py` en un portátil; 4 PCs se unen a esa IP | Funciona igual, sin juego abierto en el servidor | |

**Si A1–A3 fallan:**
1. Revisar que los equipos estén en la misma red y que el wifi no aísle a los clientes. El wifi de invitados suele hacerlo.
2. Revisar el firewall de Windows: Configuración → Firewall → permitir DigitalMayor en redes privadas.

## B. Arena Online (teléfonos y redes distintas)

Requiere que el backend esté desplegado con la Arena Online (ver `DESPLIEGUE.md`).

| # | Paso | Esperado | Resultado |
|---|---|---|---|
| B1 | Teléfono 1 (datos móviles) abre `https://civitas-leaderboard.onrender.com/arena` | La página carga (la primera vez puede tardar ~50 s por el plan gratuito) | |
| B2 | Teléfono 1: nombre, rol → Crear sala → Copiar enlace → enviarlo por WhatsApp | Se copia `…/arena?sala=XXXXX` | |
| B3 | Teléfono 2 (otro wifi) abre el enlace, elige rol → Unirse → Estoy listo | El teléfono 1 lo ve «Listo» en 1–2 s | |
| B4 | Jugar 5 rondas con 2, 3 y 4 dispositivos (mezclar teléfonos y PC) | Mismo resultado en todos; los botones se pulsan bien con el dedo | |
| B5 | Bloquear el teléfono 2 durante 30 s y desbloquear | Vuelve a la ronda en curso sin pedir nada | |
| B6 | Recargar la página en mitad de la partida | Sigue en su puesto (reconexión automática) | |
| B7 | Intentar unirse a una sala empezada o llena | Mensaje claro («ya empezó» o «llena») | |
| B8 | Pantalla final | Votos de los 4 candidatos, explicación y clasificación de la sala | |
| B9 | Escenas: cada jugador lee su pista privada | Cada teléfono ve una pista distinta («Solo tú lo ves»); nadie ve la del otro | |
| B10 | Moderación y Rastreador con el dedo | Botones Borrar/Dejar cómodos; fichas y huecos se tocan sin errores | |
| B11 | Caza-Rumores en teléfono vertical y horizontal | Los rumores se pueden tocar; anotar fallos de puntería por tamaño | |
| B12 | Ruta de la Verdad con botones táctiles (mover y saltar a la vez) | Se puede mantener la flecha y saltar con el otro dedo; anotar si el salto se siente tardío | |
| B13 | Duelo en iPhone (Safari) y Android (Chrome), con y sin auriculares Bluetooth | La canción suena (AAC en iPhone); con Bluetooth ajustar calibración y anotar el valor | |
| B14 | Medir con reloj la duración de una partida Feria con 4 personas nuevas | Anotar minutos reales (escenas + 5 retos + 5 decisiones) | |
| B15 | Pantalla de espectadores `/arena?ver=CÓDIGO` en un PC del stand | Muestra fase, reto y clasificación; nunca las pistas privadas | |

## C. Mando, teléfono con la historia, audio

| # | Paso | Esperado | Resultado |
|---|---|---|---|
| C1 | Mando: historia completa en Modo Feria (decisiones, 5 minijuegos, pausa del duelo con Start → A, escrutinio, resultados) | Todo se maneja sin ratón | |
| C2 | Mando en la Arena local: opciones del árbol con cruceta + A | Se puede jugar | |
| C3 | Teléfono: web del juego (`ac020907.github.io/pruebaslaboratorio`) en horizontal, Modo Feria completo | Carga y se juega por toque; el sonido se activa tras el primer toque | |
| C4 | Escuchar las voces del prólogo y de los 5 finales, la música y el Duelo | Sin cortes, volumen equilibrado, nombres bien pronunciados | |
| C5 | Opciones → Accesibilidad → Avisos visuales de sonido, con el volumen en 0 | Aparecen los avisos «SONIDO …» | |
| C6 | 5 personas ajenas al equipo, según `PROTOCOLO_PRUEBAS_JUGADORES.md` | Llenar la planilla con datos reales | |

**Registro:** anotad fecha, equipos (modelo y sistema operativo) y red usada, y adjuntad fotos o vídeos de las pantallas. No marquéis OK lo que no se vio funcionar.
