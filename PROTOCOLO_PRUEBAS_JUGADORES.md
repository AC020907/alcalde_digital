# Protocolo de prueba con jugadores — Alcalde Digital (Modo Feria)

**Estado: pendiente.** Todavía no se ha probado con personas. Este documento no contiene resultados: se llenan al hacer las sesiones.

## Objetivos de experiencia (hipótesis a comprobar, no resultados)

| # | Objetivo | Cómo se mide | Meta inicial |
|---|---|---|---|
| O1 | Entiende que es el alcalde y cuál es el problema en el primer minuto | Pregunta P1 + minuto en que toma la primera decisión | 4 de 5 lo explican; primera decisión antes de 1:30 |
| O2 | Termina el Modo Feria sin ayuda del equipo | Número de intervenciones del observador | 0 intervenciones en al menos 4 de 5 |
| O3 | No encuentra bloqueos | Momentos en que no sabe qué hacer más de 20 s | Ninguno de más de 60 s |
| O4 | Entiende al menos una consecuencia de sus decisiones | Pregunta P4 | 4 de 5 nombran una decisión y su efecto |
| O5 | Encuentra una razón para repetir | Pregunta P8 | Media ≥ 3,5 de 5 y al menos una razón concreta |
| O6 | Duración razonable | Cronómetro | 9–13 min (el guion medido de un recorrido son ~1.000 palabras y 5 minijuegos) |

## Participantes

5 personas que no conozcan el proyecto. Al menos una que no juegue habitualmente y una que juegue con **mando**. Si es posible, una en **teléfono** (versión web, en horizontal).

## Preparación

1. Borrar el progreso de prueba (lanzador de Ren'Py → *Delete Persistent*), así el Archivo de Destinos empieza vacío.
2. Abrir **Modo Feria (12 min)**. Volumen al 70 %, en un sitio sin mucho ruido, para poder juzgar voces y música.
3. Decir solo: "Eres el alcalde de una ciudad durante una semana de rumores. Juega como quieras; si algo no se entiende, dilo en voz alta". No explicar controles, minijuegos ni el expediente.
4. Una copia de esta hoja por jugador y un cronómetro.

## Durante la partida (observar sin intervenir)

| Medida | J1 | J2 | J3 | J4 | J5 |
|---|---|---|---|---|---|
| Dispositivo (PC ratón / PC mando / teléfono) | | | | | |
| Minuto de la primera interacción (primer clic o tecla) | | | | | |
| Minuto de la primera decisión | | | | | |
| ¿Entendió los controles sin ayuda? (mapa, teléfono) | | | | | |
| ¿Abrió CivitasNet o el expediente por su cuenta? | | | | | |
| Moderación: resultado y si entendió borrar/aprobar | | | | | |
| Caza-Rumores: resultado y si entendió el objetivo | | | | | |
| Rastreador: tiempo, pistas usadas, si entendió la cadena | | | | | |
| Duelo de Frecuencias: dificultad elegida, nota, ¿pausó?, ¿notas adelantadas/atrasadas? | | | | | |
| Gran Viralización: resultado | | | | | |
| Decisión del audio de Tomás: qué eligió y cuánto dudó | | | | | |
| Final obtenido y puntuación | | | | | |
| Duración total | | | | | |
| Intervenciones del observador (minuto y motivo) | | | | | |
| Momentos de duda > 20 s (minuto y qué pasaba) | | | | | |
| Errores de navegación (botón equivocado, menú que no esperaba, pantalla sin salida) | | | | | |
| Pistas o fichas del expediente que no entendió (cuál) | | | | | |
| ¿Saltó voces o texto? ¿Bajó el volumen? | | | | | |

## Preguntas al terminar (3 minutos)

1. **P1.** En una frase: ¿quién eras y qué problema tenía la ciudad?
2. **P2.** ¿Qué era NOVA y qué hacía?
3. **P3.** ¿De dónde salió el rumor del agua?
4. **P4.** ¿Recuerdas una decisión tuya que haya cambiado algo después? ¿Qué cambió?
5. **P5.** ¿Qué personaje recuerdas más? ¿Por qué?
6. **P6.** ¿Qué minijuego fue el más difícil? ¿Y el más divertido?
7. **P7.** ¿Las voces y la música te ayudaron, te dieron igual o molestaron? ¿Alguna voz sonó rara?
8. **P8.** Del 1 al 5, ¿qué tantas ganas tienes de jugar otra vez? ¿Para qué?
9. **P9.** ¿El final reflejó cómo gobernaste?
10. **P10.** Del 1 al 5, ¿qué tanto te gustó la partida? ¿Qué cambiarías primero?

## Cómo leer los resultados

- **O1 falla:** reforzar el prólogo (primeras líneas de Claudia) antes de tocar el resto.
- **O2/O3 fallan en el mismo punto:** es un bloqueo de diseño. Anotar la pantalla exacta y corregir esa interfaz.
- **Duración media > 13 min:** acortar `FERIA_RASTREO` (`story/modo_feria.rpy`) o los viajes conducidos de la feria (`Misiones.FERIA_CONDUCIR`).
- **P3 sin respuesta correcta:** reforzar el texto de Claudia en `giro_nova`.
- **P7 menciona voces raras:** cruzar con `tools/voces/GRABACION_RECOMENDADA.md` y priorizar esas líneas para grabación humana.
- **Duelo: varias personas notan desfase:** ajustar `persistent.ritmo_offset_ms` por defecto en ese equipo (pausa del duelo → ±10 ms) antes de tocar los charts.
- **Mando o teléfono con problemas:** anotar la pantalla y el botón, y revisar la lista de pruebas manuales de `GAME_AUDIT.md`.
