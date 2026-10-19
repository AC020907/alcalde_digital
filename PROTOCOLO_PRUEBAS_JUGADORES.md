# Protocolo de prueba con jugadores — Alcalde Digital (modo feria)

**Estado: pendiente.** Todavía no se ha probado con personas.

## Participantes

3 a 5 personas que no conozcan el proyecto. Al menos una que no juegue habitualmente.

## Preparación

1. Abrir el juego desde el lanzador de Ren'Py y elegir **Modo Feria (8 min)** en el menú principal.
2. Tener a mano un cronómetro y esta hoja (una copia por jugador).
3. Explicar solo esto: "Eres el alcalde de una ciudad durante una semana de rumores. Juega como quieras". No explicar controles, minijuegos ni el expediente.

## Durante la partida (observar sin intervenir)

| Medida | Jugador 1 | Jugador 2 | Jugador 3 | Jugador 4 | Jugador 5 |
|---|---|---|---|---|---|
| Tiempo hasta la primera decisión (prólogo) | | | | | |
| ¿Abrió CivitasNet o el expediente por su cuenta? (sí/no) | | | | | |
| ¿Añadió alguna pista al expediente? | | | | | |
| Moderación: ¿entendió los controles sin ayuda? | | | | | |
| Caza-Rumores: ¿entendió el objetivo? | | | | | |
| Rastreador: tiempo hasta terminar (o hasta rendirse) | | | | | |
| Rastreador: ¿usó pistas? ¿cuántas comprobaciones? | | | | | |
| Gran Viralización: resultado | | | | | |
| Final obtenido | | | | | |
| Duración total de la partida | | | | | |
| Momentos de duda o abandono (minuto y qué pasaba) | | | | | |

## Preguntas al terminar (2 minutos)

1. En una frase: ¿qué era NOVA y qué hacía?
2. ¿De dónde salió el rumor del agua?
3. ¿Recuerdas alguna decisión tuya que haya cambiado algo después? ¿Cuál?
4. ¿Qué parte te pareció más divertida? ¿Y la más confusa?
5. Del 1 al 5, ¿qué tantas ganas tienes de jugar otra vez para ver otro final?

## Cómo leer los resultados

- Si la duración media supera los 9 minutos, acortar diálogos del giro o el tiempo del Rastreador en `FERIA_RASTREO` (`story/modo_feria.rpy`).
- Si nadie entiende la pregunta 2, reforzar la escena de la inferencia o el texto de Claudia en `giro_nova`.
- Si nadie abre CivitasNet por su cuenta, agregar una apertura guiada más en `modo_feria`.
