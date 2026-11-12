# Duelo de Frecuencias: modo competitivo (final del torneo)

**Recursos:** canciones, charts y sprites propios del proyecto (`game/ritmo/*.json`, `assets/audio/music/duelo_*.ogg`, `gui/ritmo/*`). No usa nada de otros juegos de ritmo.

## Juego

- **Carriles:** 4 por cliente. Se juegan con D F J K, las flechas o el mando, igual que en la Historia.
- **Chart:** el mismo para todos, `duelo_<modo>_normal.json` (98 notas en el completo y 43 en la Feria). Lo valida `Ritmo.validar_chart` en el cliente y en el servidor.
- **Juicios:** se usan las ventanas de la dificultad Normal.

| Juicio en pantalla | Interno | Ventana | Valor | Combo |
|---|---|---|---|---|
| PERFECT | `perfect` | ±45 ms | 100 % | Suma |
| GREAT | `good` | ±90 ms | 70 % | Suma |
| GOOD | `bad` | ±135 ms | 30 % | Lo rompe |
| MISS | `miss` | — | 0 % | Lo rompe |

- **Sincronía:** `Ritmo.RelojCancion` sigue la posición del audio (no el reloj del sistema) con el desfase calibrado del jugador (`persistent.ritmo_offset_ms`). Cada cliente juega con su propio audio. El torneo no exige que las canciones empiecen a la vez: compara precisión, no tiempos absolutos.

## Presentación

- **Antes del duelo:** la pantalla de la prueba lo anuncia como «PRUEBA 5 DE 5 · FINAL», con el botón «¡AL DUELO FINAL!». Después, `arena_duelo_intro` muestra el título animado, el número de notas, los cuatro juicios con su color y los controles.
- **Durante el duelo:** NOVA y el aliado reaccionan a los combos, como en la Historia.
- **Después del duelo:**
  - `arena_resumen_prueba`: barras por jugador con precisión y combo máximo, y la clasificación acumulada. El botón del anfitrión pasa a «Ver la elección ›».
  - `arena_final_torneo`: campeón con animación, desglose por prueba, ganadores de cada prueba, elección y resultado de la ciudad.

## Puntuación en el servidor

`torneo.puntuar_ritmo`:
1. Exige `dificultad == "normal"` y exactamente un juicio válido por nota del chart.
2. Recalcula la precisión, `Σ valor(juicio) / notas`.
3. Recalcula el combo máximo (solo `perfect` y `good` lo encadenan).
4. Puntúa con `850·precisión + 150·combo_máx/notas`. Un juego perfecto da 1000.

Las notas que el cliente no juzgó (por ejemplo, si abandonó) se envían como `miss`.

## Limitación

El instante de cada pulsación se mide en el cliente. El servidor no puede distinguir unos juicios reales de unos inventados que sean coherentes. Mitigaciones:
- longitud exacta del chart;
- dificultad fija;
- combo recalculado.

En una LAN de laboratorio se considera suficiente. Ver `ARENA_TORNEO.md` §Limitaciones.

## Online: el Duelo en la Arena por navegador

En la Arena Online (`/arena`) el Duelo es la **gran final**. Se juega al abrir la última ronda; después vienen la última decisión cívica, sus consecuencias, la elección y el campeón. Cada jugador usa su teléfono o computador.

**Qué se reutiliza (una sola fuente):**

| Pieza | Origen | En el navegador |
|---|---|---|
| Chart | `game/ritmo/duelo_<modo>_normal.json` | `GET /api/arena/ritmo/<modo>` lee el mismo archivo |
| Ventanas y valores de juicio | `Ritmo.VENTANAS_MS`, `Ritmo.VALOR_JUICIO` | Los envía el servidor; el JS no tiene números propios |
| Lógica de notas (`Duelo.pulsar`, `actualizar`, combo) | `clases/Ritmo.py` | `static/ritmo_motor.js`, traducción 1:1 |
| Puntuación | `torneo.puntuar_ritmo` | Misma fórmula en vivo; al final coincide con la del servidor |
| Música, notas, receptores y NOVA | `game/assets`, `game/gui/ritmo`, sprites | `tools/web/exportar_ritmo_online.py` los copia a `static/ritmo/`; la música va también en AAC porque Safari no reproduce OGG |
| Recorrido de 1500 ms, expresiones de NOVA, barra señal/interferencia | `minijuegos/ritmo.rpy` | Iguales en el canvas |

**Contrato de equivalencia:** `tests/test_ritmo_web.py` ejecuta `ritmo_motor.js` en Node y `Ritmo.Duelo` en Python con las **mismas** pulsaciones. Lo hace a 30, 60 y 144 Hz con jitter, en los dos charts y con 3 niveles de habilidad. Coinciden juicio a juicio, en combo máximo, precisión y estado final. Además, el servidor acepta lo que produce el navegador y le da los mismos puntos.

**Sincronización (sin enviar notas por internet):**
1. **Inicio común:** el servidor fija `inicio`, 9 s después de abrir el duelo (cuenta atrás común). Cada respuesta del sondeo (cada 1 s) trae «faltan X ms».
2. **Reloj del servidor:** el navegador estima el instante local de inicio con la muestra de **menor ida y vuelta**: `recibido − RTT/2 + faltan`, tomando la mediana de las 3 mejores muestras (`SyncReloj`).
3. **Arranque del audio:** 2,5 s antes del inicio, programa la canción con Web Audio en ese instante (`source.start(t)`). Quien llega tarde (por ejemplo, tras recargar) entra en la posición actual de la canción; lo pasado cuenta como MISS.
4. **Juicio:** se hace con el **reloj de audio**: `(ctx.currentTime − inicio)·1000 − latencia de salida − calibración`. Los frames solo dibujan.
5. **Calibración:** ±10 ms por pulsación antes de empezar; se recuerda en el teléfono.

**Validación** (`clases/arena/duelo_online.py`): el navegador envía, por nota, el juicio y su desvío en ms. El servidor:
- exige la longitud exacta del chart y la dificultad Normal;
- comprueba que cada juicio corresponda a su desvío (±1 ms de redondeo) y que un MISS no tenga desvío;
- rechaza resultados llegados **antes** de que sonaran sus notas;
- acota la calibración a ±300 ms;
- rechaza patrones imposibles para una persona (dispersión de desvíos < 2,5 ms en 20 notas o más);
- recalcula puntos, combo y precisión.

**Robustez:**
- **Entrega:** es idempotente (mismo `id`) y se reintenta si falla la red; una segunda entrega distinta se rechaza.
- **Pausa:** no hay; la canción suena para todos a la vez.
- **Desconexión:** quien no entrega al vencer el margen (canción + 12 s) recibe 0.
- **Jugadores automáticos:** juegan con desvíos gaussianos.
- **Marcador en vivo:** cada teléfono envía puntos y combo cada 1,5 s para que lo vean los rivales. Solo se muestra; no puntúa.

**Pruebas:**

| Comando | Qué cubre |
|---|---|
| `cd leaderboard && python -m pytest -q tests/test_arena_duelo_online.py` | 10 pruebas con reloj simulado: 2, 3 y 4 clientes con el mismo inicio, puntos recalculados por el servidor, entrega tardía por latencia, desconexión, pausa rechazada, reconexión, 6 manipulaciones, duplicados, bots y configuración tomada del juego |
| `python -m pytest -q tests/test_ritmo_web.py` | Equivalencia JS/Python a 30, 60 y 144 Hz; sincronización con latencia simulada (asimetría y picos) |
| `python tests/e2e_arena_online.py --jugadores 2,3,4` (antes `e2e_duelo_online.py`, sustituido por la campaña completa) | Chrome real (headless) con 2, 3 y 4 navegadores aislados (PC y móvil táctil) y latencia de 0, 60, 180 y 400 ms por jugador (CDP). Ver detalle abajo |

Detalle de la prueba del duelo (2026-11-09, antes de la campaña):
- **Juego:** juega el Consejo con clics, entra al duelo con el botón, reproduce la canción por Web Audio y pulsa por el mismo camino que un dedo. Cada jugador tiene un error humano distinto (`?autoplay=1`, solo en localhost).
- **Comprobaciones:** la final es idéntica en todos y los puntos del navegador coinciden con los del servidor.
- **Casos especiales:** recarga a mitad de canción (el jugador vuelve a entrar) y desconexión a mitad de canción (recibe 0).
- **Resultado del 2026-11-09:**
  - 2 jugadores: 1000 / 759 (con recarga).
  - 3 jugadores: 1000 / 798 / 0 (con desconexión).
  - 4 jugadores: 1000 / 789 / 637 / 411.
  - En los tres casos, misma final en todos los navegadores.

**Limitaciones:**
- **Momento de cada pulsación:** lo mide el teléfono. Un cliente modificado que invente desvíos plausibles no se distingue de una persona; la validación sube el coste de hacer trampa, pero no lo hace imposible.
- **Latencia asimétrica:** cada teléfono puede arrancar desfasado de los demás hasta la mitad de la asimetría (en la prueba, de 100 a 200 ms con 180–400 ms emulados). No afecta a la puntuación, porque cada uno juzga contra su propio audio.
- **Pestaña en segundo plano:** si el sistema suspende el audio, la canción de ese jugador se detiene. Al vencer el margen se envía lo jugado y el resto cuenta como MISS.
- **Sin probar en dispositivos reales:** iPhone/Safari (AAC), Android/Chrome y auriculares Bluetooth (ver `docs/PRUEBAS_FISICAS.md`).
