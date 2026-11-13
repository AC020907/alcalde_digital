# Ruta de la Verdad: infiltración NOVA (plataformero 2D)

## Por qué existe

La Gran Viralización usaba la misma clase (`CazaRumores`) y la misma pantalla (`jugar_arcade`) que Caza-Rumores: eran dos arcades de apuntar casi iguales. Ahora:

- **La crisis narrativa se mantiene.** NOVA despierta todas sus cuentas el domingo a las 6:00, y los aliados de la semana siguen ayudando o estorbando.
- **La respuesta del jugador cambia.** Ya no apunta a rumores: entra al sistema de NOVA, esquiva sus defensas y rescata los fragmentos de evidencia original.

Para no romper nada:

- El label `evento_gran_viralizacion` se mantiene.
- La clave del resultado sigue siendo `"viralizacion"`. Por eso finales, expediente, Puntuación Cívica, registros y guardados no cambian.
- El arcade de punteria queda solo en Caza-Rumores.

## Mecánicas

| Elemento | Detalle |
|---|---|
| Movimiento | Izquierda y derecha con aceleración y freno |
| Salto | Único, sin doble salto. Es variable: si se suelta antes, se corta |
| Coyote time | 6 ticks (100 ms): se puede saltar justo después de dejar el borde |
| Jump buffering | 7 ticks (~117 ms): un salto pulsado justo antes de aterrizar se ejecuta al tocar suelo |
| Colisiones | Resueltas por ejes contra una rejilla de tiles. La velocidad máxima es menor que un tile, así que no hay «túneles» |
| Corrección de esquina | Si la cabeza roza el borde inferior de un bloque (hasta 7 px), el salto no se corta: el personaje se desliza a un lado (`test_correccion_de_esquina_y_aterrizaje`) |
| Aterrizaje | Evento `aterriza` para el polvo y la animación; igual en el navegador |
| Peligros | Pinchos (la caja de daño es menor que el tile), caída al vacío y bloques intermitentes `~` que avisan medio segundo antes de cambiar, con color y forma |
| Puntos de control | Al morir se reaparece en el último, tras 0,6 s de reaparición |
| Coleccionables | 5–8 fragmentos de evidencia con significado narrativo (factura de Resonancia, lista de bots, análisis original del Acueducto…) |
| Fin | Meta (archivo recuperado), tiempo agotado o abandono |
| Controles | Teclado (A/D, flechas, Espacio/W), mando (cruceta + A), táctil (botones en pantalla, multitoque) |

## Presentación (Ren'Py y web)

- **Escala:** tiles de 72 px en 1920 × 1080; el nivel ocupa el alto útil.
- **Cámara:** sigue al jugador con suavizado, respeta los límites y mira 260 px hacia donde corre para ver antes los obstáculos. Con «reducir movimiento» no hay suavizado.
- **Partículas moderadas:** polvo al saltar y aterrizar, destellos dorados al recoger evidencia, chispas rojas al ser detectado y una explosión turquesa en la meta. Con «reducir movimiento» se reducen a un tercio.
- **Victoria:** destello, el texto «ARCHIVO RECUPERADO» y, tras 1,1 s, la pantalla de resultados (puntos, evidencias, detecciones, tiempo y la lista de documentos recuperados).
- **Pausa** (botón, Esc/P o Start) con **reinicio rápido** en Historia y Feria. En la Arena no se puede reiniciar: todos tienen un solo intento.
- **Rendimiento:** 178 FPS medidos en el motor real con la QA de minijuegos (RTX 4070, 1920 × 1080).
- **Plataformas móviles: no se añadieron.** Los huecos, fosos, torres y bloques intermitentes ya dan variedad. Plataformas móviles exigirían arrastrar al jugador y complicarían la paridad con el motor web, sin mejorar claramente el juego.

## Consecuencias narrativas

Al salir del sistema de NOVA, Claudia reacciona según lo recuperado (`label evidencias_rescatadas`, Historia y Feria):

| Lo recuperado | Reacción y efecto |
|---|---|
| Todo | Publica el desmentido con cada documento: información verificada +3, confianza +2 |
| Al menos la mitad | Puede desmentir lo principal: información verificada +1 |
| Menos de la mitad | Hay que desmentir sin pruebas; sin bonificación |

Las tres líneas están dobladas con ElevenLabs. Fallar no bloquea la historia.

## Física determinista

El motor (`game/clases/Plataformas.py`) usa un paso fijo de 60 ticks por segundo y **solo enteros**, con subpíxeles de 1/16 px.

- **Render:** Ren'Py y el navegador acumulan tiempo real y avanzan ticks enteros. Tras un tirón de más de 100 ms no hay teletransporte.
- **Independencia de los FPS:** a 30, 60 o 144 FPS se simulan exactamente los mismos ticks (`test_independiente_de_los_fps`).
- **Navegador:** `leaderboard/app/static/plat_motor.js` es una traducción 1:1. Las constantes y el mapa los envía el servidor (`config_cliente`), así que no hay números duplicados. `tests/test_plataformas_web.py` compara Node con Python tick a tick (posición, velocidad, muertes, evidencias, estado, puntos y traza) en los cuatro niveles.

## Niveles

Los niveles se arman con tramos probados una vez: inicio, huecos de 2 y 3, fosos de pinchos, escalón, torre, puente intermitente, evidencia alta, punto de control y meta.

| Nivel | Uso | Tiempo | Evidencias |
|---|---|---|---|
| `tutorial` | — | 60 s | 4 |
| `historia` | Historia (domingo) | 120 s (+/− ayuda de aliados, máximo ±40 s) | 8 |
| `arena` | Torneo LAN completo | 80 s | 6 |
| `feria` | Modo Feria, torneo Feria y Arena Online | 55 s | 5 |

`test_todos_los_niveles_se_pueden_completar_con_todas_las_evidencias` lanza pilotos automáticos en cada nivel y exige que alguno llegue a la meta y que cada evidencia la recoja al menos uno.

**Ayuda narrativa (solo Historia):** el aliado del domingo, que antes subía el umbral viral, ahora da segundos extra (`extra_plataformas`). El video patrocinado de Martina los quita. En la Arena es siempre 0, para que todos jueguen en las mismas condiciones.

## Puntuación (0–1000)

```
evidencias = 550 · recogidas / total        (dominan)
si llega a la meta:
    + 250                                   (completar)
    + 150 · tiempo_sobrante / tiempo_total  (desempate)
    + max(0, 50 − 10 · detecciones)         (ajuste moderado)
```

Reglas que impiden aprovecharse del sistema:
- Sin llegar a la meta no hay bonos ni victoria.
- Cada evidencia cuenta una vez, aunque el jugador muera y vuelva a pasar.
- Las muertes solo restan hasta 50 puntos.

**Contrato de resumen:** `score_raw`, `score_normalized`, `completed`, `evidence`, `deaths`, `elapsed_ms`.

**Nota de la Historia:** S ≥ 900, A ≥ 780, B ≥ 640 y C si llega a la meta. Las consecuencias sobre la ciudad son las mismas que tenía la Gran Viralización.

## Multijugador

- **Torneo LAN:** el cliente Ren'Py envía su `traza` (pares `[máscara, ticks]`). El servidor la rejuega con `Plataformas.rejugar` y puntúa. Rechaza máscaras fuera de rango, trazas más largas que el nivel o con formato inválido. Si la traza termina antes de tiempo, cuenta como abandono: solo vale lo conseguido.
- **Arena Online:** igual, con una comprobación más. La duración de la traza no puede superar el tiempo real transcurrido desde la salida, más la tolerancia de sincronización.

## Arte

Todo es original y lo genera `tools/arte/plataformero.py` con dibujo vectorial en PIL. El estilo mezcla dos mundos:

- **Personaje cálido y pastel:** capucha crema, bufanda vino y cuerpo violeta.
- **Sistema de NOVA oscuro y neón:** tiles, pinchos magenta, bloques intermitentes, fondos de torres de servidores con parallax y el portal del archivo.

Los sprites incluyen reposo, carrera (4 cuadros), salto, caída y daño.

## Pruebas

| Comando | Qué cubre |
|---|---|
| `python -m pytest -q tests/test_plataformas.py` | 21 pruebas: niveles alcanzables, gravedad, paredes, salto único y variable, coyote, buffer, caída, punto de control, intermitentes, puntuación, contrato, ayuda acotada, rejuego exacto, trazas manipuladas e independencia de los FPS |
| `python -m pytest -q tests/test_plataformas_web.py` | Paridad tick a tick JS/Python en 4 niveles × 4 perfiles de entrada |
| `python tests/qa_visual.py galeria --etapas minijuegos` | Motor real de Ren'Py: tutorial, cuenta atrás, juego y resultado (piloto automático). Capturas en `docs/auditoria/plat_*.jpg` |

**Limitación:** el piloto automático de la QA no mide si la curva de dificultad es divertida. Falta jugarlo con personas (ver `docs/PRUEBAS_FISICAS.md`).
