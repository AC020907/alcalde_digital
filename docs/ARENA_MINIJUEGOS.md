# Minijuegos como pruebas de la Arena

Cada prueba reutiliza el **mismo label** de la Historia, con `aplicar=False` para que no toque la partida de la Historia y con la semilla y los ajustes que envía el servidor. El cliente envía **qué decidió**; el servidor lo vuelve a puntuar con el motor de la prueba.

| Prueba | Label (cliente) | Qué envía el cliente | Qué hace el servidor | Puntuación 0–1000 |
|---|---|---|---|---|
| Moderación Express | `minijuego_moderador(semilla, False, cantidad)` | `decisiones`: lista de bool (borrar o aprobar), en orden | Regenera la cola con `publicaciones_moderacion(semilla)` (`clases/moderacion_datos.py`) y la **rejuega** en `ColaModeracion`. Las tarjetas sin decidir cuentan como aprobadas (lo mismo que hace el tiempo en el juego) | `1000·aciertos/total − 120·censuras − 60·bots colados`. Censurar una crítica real pesa más |
| Caza-Rumores | `minijuego_contencion(focos, semilla, False, ajustes)` | `reposts`, `interceptados`, `exito` | Reconstruye `CazaRumores` con los mismos focos y ajustes para conocer la base y el umbral. Rechaza valores fuera de rango y «contenido» con viralidad ≥ 100 % | `650·(1−viralidad) + 250·contenido + min(100, 4·interceptados)` |
| Rastreador | `minijuego_rastreador(semilla, False, ajustes)` | `intentos` (cada comprobación: cadena + conclusión, guardada en `PuzzleEvidencias.intentos`), `pistas`, `segundos` | **Rejuega** cada intento en un `PuzzleEvidencias` con la misma semilla. Decir «lo encontré» no basta: la cadena tiene que ser correcta | Éxito: `620 + 380·(1 − t/T) − 70·pistas − 60·(comprobaciones − 1)`, mínimo 250. Fallo: `100·eslabones correctos` |
| Ruta de la Verdad (plataformas) | `minijuego_plataformas(nivel, False)` | `traza`: entradas por tick comprimidas ([máscara, ticks]) | **Rejuega** la carrera con `Plataformas.rejugar` (motor entero a paso fijo) | Ver `PLATAFORMERO_RUTA_VERDAD.md`: evidencias 550, meta 250, tiempo hasta 150, detecciones hasta 50 |
| Duelo de Frecuencias (final) | `minijuego_ritmo(modo, False, None, "normal")` | `dificultad` = «normal» y `juicios`: uno por nota del chart | Carga el chart del servidor. Exige exactamente una entrada por nota y recalcula precisión, conteo y combo máximo | `850·precisión + 150·combo_máx/notas` (ver `ARENA_RITMO_MULTIJUGADOR.md`) |

## Condiciones equivalentes

- **Semilla:** una por prueba, igual para todos (`Random("torneo|<semilla de la partida>|<prueba>")`).
- **Ajustes:** salen de los indicadores **compartidos** del Consejo, así que son iguales para todos.
- **Duelo:** siempre en Normal, con el mismo chart. El jugador no elige dificultad en el torneo.
- **Accesibilidad:** el modo asistido de la Historia no está disponible en el torneo, para no mezclar condiciones. Los avisos visuales de sonido, los subtítulos y «reducir movimiento» siguen activos porque no cambian la dificultad.

## Cambios en los minijuegos (sin alterar la Historia)

- `clases/moderacion_datos.py`: los comentarios y su generador salen del `.rpy` para que el servidor los pueda regenerar. `moderador.rpy` los importa.
- `PuzzleEvidencias.intentos`: guarda cada comprobación. Solo añade un registro; no cambia las reglas.
- `minijuego_ritmo(..., dificultad=None)`: si recibe una dificultad, omite el tutorial-selector. La Historia no pasa este parámetro.
- `texto_juicio()` y `duelo_competitivo`: en la Arena el Duelo muestra PERFECT, GREAT, GOOD y MISS. En la Historia siguen ¡PERFECTO!, BIEN, JUSTO y FALLO.

**Regresión:** `python tests/qa_recorridos.py` (los 5 finales en historia y en feria) y `python -m pytest -q tests`.
