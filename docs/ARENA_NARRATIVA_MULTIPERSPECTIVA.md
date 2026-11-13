# Arena Online narrativa: una historia, cuatro perspectivas

La Arena Online ya no es una serie de preguntas: es una campaña corta de 5 rondas sobre la misma crisis de Ciudad Nova.

- **Historia compartida:** todos viven la misma historia y la misma ciudad.
- **Pistas privadas:** cada rol recibe pistas que los demás no ven.
- **Retos para todos:** todos juegan los cinco retos.
- **Decisiones cívicas:** después de cada reto se decide qué hacer con lo que circula en Civitas.

Las reglas son las mismas de la Arena local (`reglas.py`): árbol de decisiones por rol, grafo social, propagación BFS, eventos, indicadores y elección.

## Bucle de una ronda

```
escena          escena común (narrador, CivitasNet, NOVA, personajes) + pista privada SOLO para tu rol
  └─ reto       los 2–4 jugadores juegan el mismo minijuego, con la misma semilla y el mismo escenario
      └─ reto_resultado   puntos 0–1000, ganador, cambios en la ciudad y clasificación acumulada
          └─ ronda        decisión cívica (árbol del rol) sobre una publicación ligada a lo vivido
              └─ resultado  propagación BFS por el grafo, indicadores, puntos cívicos
                  └─ siguiente escena … y al final la elección
```

Las fases tienen tipo y las controla el servidor: `lobby → escena → reto → reto_resultado → ronda → resultado → … → final`.

- **Escena:** avanza cuando todos los humanos pulsan «Listo» o cuando pasan 40 s.
- **Reto:** se cierra cuando entregan todos los humanos conectados o cuando vence su plazo (duración + 12 s). Quien no entrega recibe 0, y los jugadores automáticos juegan su propia partida.

## Guion (`game/clases/arena/campana.py`)

| Ronda | Protagonista | Reto | Evento de la decisión | Acontecimiento |
|---|---|---|---|---|
| 1 · Lunes | Ciudadano (Rodrigo) | Moderación Express | Discusión | El muro del barrio se llena de bots, insultos y críticas reales |
| 2 · Martes | Periodista (Claudia) | Rastreador | Noticia falsa | Reconstruir la cadena del rumor hasta su origen |
| 3 · Jueves | Candidato (Tomás) | Caza-Rumores | Rumor sobre un candidato | Un audio falso durante el debate |
| 4 · Domingo 6:00 | Influencer (Martina) | Ruta de la Verdad | Publicación viral | La Gran Viralización: entrar al sistema de NOVA |
| 5 · Domingo 7:30 | Todos contra NOVA | Duelo de Frecuencias | Noticia verdadera | NOVA secuestra la transmisión electoral |

**Pistas privadas:** cada rol recibe la voz de su personaje de la Historia (Ciudadano: Rodrigo, Periodista: Claudia, Influencer: Martina, Candidato: Tomás).

- **Información:** las pistas dan contexto complementario (por ejemplo, las fechas de las cuentas, el salto de alcance o la hora de cada reenvío), pero nunca la solución del reto.
- **Roles ausentes:** si el rol protagonista no está en la sala, el personaje aporta su línea (`ausente`) y la historia sigue.
- **Poder del rol:** el protagonista no tiene ventaja en el reto. Su poder está en sus decisiones cívicas (habilidades de `reglas.py`).

## Los cinco retos online

Ninguno es un cuestionario. Cada uno tiene una entrada, unas reglas y una forma de feedback distintas, y lo puntúa el servidor:

| Reto | En el navegador | Qué envía el cliente | Qué hace el servidor |
|---|---|---|---|
| Moderación Express | Feed de comentarios con tiempo por tarjeta; Borrar o Dejar (botones o flechas) | Cada decisión, en orden | La juzga con `ColaModeracion`. El cliente nunca sabe de antemano quién es bot |
| Rastreador | Tablero de cuentas (hora, antigüedad, seguidores), huecos de la cadena y conclusión; se toca la ficha y luego el hueco | «Comprobar» con la cadena, o «Pista» con el tablero actual | El tablero vive en el servidor (`PuzzleEvidencias`), que corrige con DFS. El origen nunca viaja al cliente |
| Caza-Rumores | Mapa del grafo social; tocar cada rumor mientras viaja por una conexión | Intercepciones `[tick, paquete, x, y]` y fallos | Rejuega la propagación (`caza_web.py`) y comprueba que cada toque cayó sobre un rumor en vuelo |
| Ruta de la Verdad | Plataformero con lienzo, parallax y controles táctiles | Traza de entradas | La rejuega con `Plataformas.rejugar` |
| Duelo de Frecuencias | 4 carriles, música, PERFECT/GREAT/GOOD/MISS | Juicio y desvío por nota | Valida contra el chart y el reloj de la sala (`duelo_online.py`) |

**Paridad con Python:**
- `caza_motor.js`, `plat_motor.js` y `ritmo_motor.js` son traducciones de los motores Python. Las pruebas `test_caza_web.py`, `test_plataformas_web.py` y `test_ritmo_web.py` los comparan con Node tick a tick.
- Los escenarios (grafo, focos, mapa, chart) y las constantes los envía el servidor, así que no hay números duplicados en el cliente.

**Sincronización:** el servidor fija el inicio de cada reto y lo comunica como «faltan X ms». El cliente estima su desfase con la muestra de menor tiempo de ida y vuelta (`SyncReloj`), hace una cuenta atrás común y juega con su propio reloj. Ningún reto envía datos por cada frame.

## Puntuación y resultados

- **Torneo:** el Consejo vale de 0 a 2000 y cada reto de 0 a 1000, con un máximo de 7000. Ninguna prueba puede decidir sola por escala.
- **Consecuencias:** la media del grupo en cada reto cambia los indicadores compartidos (la misma tabla `EFECTO` del torneo LAN), y eso influye en la elección.
- **Final:** tres resultados separados: **campeón del torneo** (individual), **ganador electoral** y **estado de Ciudad Nova** (colectivo). Si el grupo difundió mentiras, el campeón puede ganar mientras la ciudad termina en caos; el mensaje final lo dice.

## Seguridad y privacidad

- **Pistas privadas:** las calcula el servidor por jugador (`campana.escena(ronda, rol, ...)`). La vista de otro jugador y la de espectadores no las contienen; `test_pistas_privadas_solo_llegan_a_su_rol` lo comprueba con 4 roles en las 5 rondas.
- **Espectadores** (`/arena?ver=CÓDIGO`, API `GET /salas/{c}/publico`): muestran fase, reto, quién terminó, marcador en vivo, clasificación y final, sin árboles ni pistas.
- **Mensajes:** son idempotentes por reto (mismo `id` = misma entrada). Se rechazan una segunda entrega, una entrega anterior a que pueda haberse jugado (traza o intercepciones más largas que el tiempo real) y el formato inválido. Los retos no se pueden pausar.
- **Datos personales:** no se guardan. Solo un nombre visible; las salas viven en memoria y caducan a las 2 horas.

## Pruebas

| Comando | Resultado |
|---|---|
| `cd leaderboard && python -m pytest -q tests/test_arena_campana.py` | 12 pruebas con reloj simulado y API real (ver detalle abajo) |
| `python tests/e2e_arena_online.py --jugadores 2,3,4` | Chrome real (headless) con 2, 3 y 4 navegadores aislados, PC y móvil táctil, latencia de 0–350 ms por jugador y una recarga a mitad de Caza-Rumores con 3 jugadores. Campaña completa; misma final en todos |

Las 12 pruebas de `test_arena_campana.py` cubren:
- la campaña completa con 2, 3 y 4 jugadores;
- que las pistas privadas no se filtren y que un rol ausente no bloquee la historia;
- que la escena avance sola;
- que la Moderación no revele la respuesta;
- que la pista del Rastreador use el tablero actual;
- manipulaciones y entregas antes de tiempo;
- desconexión y jugadores automáticos;
- la sala clásica y la pantalla de espectadores.

**Limitaciones:**
- **Trampas:** el instante de cada acción en tiempo real lo mide el cliente. El rejuego impide resultados imposibles, pero no un cliente modificado que juegue «perfecto» de forma plausible.
- **Dispositivos:** falta probar en teléfonos reales y con personas (ver `docs/PRUEBAS_FISICAS.md`).
