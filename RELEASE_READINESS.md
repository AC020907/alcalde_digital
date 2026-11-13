# Release readiness: auditoría final, pulido visual y certificación jugable

> **Estado actual:** ver [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md), con la rúbrica y la Arena multijugador (2026-11-07). Este archivo conserva la auditoría del 2026-11-05.

- **Rama:** `qa/auditoria-final` (sale de `main` `a789ef6`, que es lo publicado hoy).
- **SDK:** Ren'Py 8.5.3.
- **Fecha:** 2026-11-05.
- **Estado: publicada** con autorización. `main` `aae3248`; web en `gh-pages` `bb1cc1c` (arranca y precarga voces e imágenes). Render sigue necesitando un *Manual Deploy* de `main` para `/static/qr.png`.
- **Veredicto:** **GO condicionado** (ver §9).

## 1. Baseline (antes de tocar nada)

| Comprobación | Resultado |
|---|---|
| Ren'Py Lint | Sin errores |
| `pytest tests` (lógica, finales, duelo) | 77 OK |
| `pytest leaderboard` | 142 OK |
| Web publicada | 200. `game.zip` 10,7 MB, de ellos 3,05 MB `main_menu.png` |
| Backend Render | `{"ok":true,"db":"ok"}` |

## 2. Cómo se auditó (motor real, no solo código)

- **`tests/qa_visual.py recorrido`:** juega el guion real de cada perfil a velocidad de lectura y saca una captura por línea.
- **`tests/qa_visual.py galeria`** (`game/qa_galeria.rpy`): fotografía por etapas:
  - menús;
  - escenas, teléfono, CivitasNet, expediente vacío, parcial y completo, mapa;
  - los 5 minijuegos jugados con entradas de mando simuladas o jugador automático: victoria, derrota, error y abandono;
  - las 5 pantallas de final con los 5 estados de envío.
- **Verificación automática** de cada etapa: que no se bloquee, el final esperado, que cada minijuego devuelva el control, el resultado del duelo y el historial. Se cumple con salida 0.
- **Hojas de contacto:** se generan junto a las capturas.
- **Resoluciones:** 1920×1080, que Windows ajusta a 1739×978 en ventana (misma proporción 16:9); 1366×768; y 1600×720 con la variante táctil/móvil de Ren'Py (20:9, teléfono en horizontal).

## 3. Matriz de cobertura

| Etapa | 1920×1080 (1739×978) | 1366×768 | 1600×720 táctil |
|---|---|---|---|
| Menús, guardar/cargar, historial, ayuda, archivo, clasificación, alias | OK | OK | OK |
| Escenas, teléfono, CivitasNet, expediente, mapa | OK | **Sin ejecutar**: la instancia no arrancó con 10 en paralelo; hay que repetirla | OK |
| 4 minijuegos (Moderación, Caza-Rumores, Gran Viralización, Rastreador) | OK | OK | OK |
| Duelo (perfecto con pausa) | Las 6 capturas, incluido el resultado, se tomaron, pero se agotó el límite de tiempo del QA con 10 instancias a la vez. Por separado da S 97 % | S 97,7 % | S 97,6 % |
| 5 pantallas de final | OK | OK | OK |
| Recorridos de los 5 perfiles (feria) | OK, 5 finales | — | — |

**Pendiente de repetir (en solitario):** `python tests/qa_visual.py galeria --tam 1366x768 --etapas escenas` y `--etapas ritmo` a 1920.

## 4. Hallazgos y correcciones

El detalle técnico (causa raíz y corrección) está en `GAME_AUDIT.md` §12. Resumen:

| P | Hallazgo | Estado |
|---|---|---|
| P0 | El duelo se congelaba tras Pausa → CONTINUAR | Corregido y verificado: perfecto con pausa da S, 97 % |
| P1 | Moderación: con mando, A no salía de resultados (foco en BORRAR/APROBAR) | Corregido y verificado: los 4 minijuegos devuelven el control con A |
| P2 | Tutorial y pausa del duelo: botones fuera del panel | Corregido |
| P2 | Guardar, Cargar, Ayuda y confirmaciones en inglés | Corregido (`tl/spanish` del SDK). Voces verificadas |
| P2 | Rótulo del mapa detrás de Rodrigo (Barrio Sur) | Corregido |
| P2 | Textos sin tildes en CivitasNet, avisos y arcades | 47 líneas corregidas |
| P3 | Notas del duelo sobre la cabecera y congeladas al abandonar | Corregido |
| P3 | 3,8 MB de PNG opacos en la descarga web inicial | Pasados a JPG: −3,0 MB |
| P3 | EMPEZAR del Rastreador con el estilo por defecto | Corregido |
| P3 | No hay opción propia de tamaño de texto | Abierto. Ren'Py la ofrece en Shift+A (accesibilidad) |

**Abiertos P0/P1:** ninguno conocido.

## 5. Capturas antes/después

Composiciones en `docs/auditoria/` (excluido de las builds):

| Archivo | Qué muestra |
|---|---|
| `01_barrio_sur_rotulo.jpg` | Rótulo "BARRIO" detrás de Rodrigo → plano limpio |
| `02_duelo_tras_pausa_congelado.jpg` | Notas congeladas 40 s después de reanudar → duelo en marcha |
| `03_duelo_tutorial_desborde.jpg` | Texto y botones fuera del panel → dentro |
| `04_duelo_pausa_desborde.jpg` | Fila de velocidades fuera del panel → dentro |
| `05_moderador_resultado.jpg` | Tarjeta visible a través del panel y botón azul → panel limpio |
| `06_guardar_ingles.jpg` / `07_ayuda_ingles.jpg` | "Page 1", "empty slot", ayuda en inglés → español |

## 6. Comandos ejecutados y resultados

```bash
renpy.exe . lint                                   # sin errores (antes y después)
python -m pytest -q tests                          # 77 OK
cd leaderboard && python -m pytest -q              # 142 OK
python tests/qa_visual.py recorrido --salida <dir>                       # 5 perfiles, 5 finales
python tests/qa_visual.py galeria --tam 1920x1080,1366x768 --salida <dir>
python tests/qa_visual.py galeria --tam 1600x720 --movil --salida <dir>
python tests/qa_visual.py galeria --etapas ritmo:nada,ritmo:abandonar,dialogo:w,dialogo:nw --salida <dir>
```

- **`qa_visual.py`:** sale con 1 si alguna etapa se bloquea o da un resultado inesperado.
- **Aislamiento:** los recorridos y la galería usan un `--savedir` aislado y apartan `game/saves`, así que nunca tocan el progreso real ni el servidor de producción.
- **Simulación de balance** (Gran Viralización sin intervenir, `CazaRumores` puro): historia 0/15 victorias, feria 1/15.

## 7. Cinco finales y cinco minijuegos

**Finales**, alcanzados con renderizado real en modo feria (`qa_visual.py recorrido`):

| Perfil | Final | Capturas |
|---|---|---|
| investigador | Fuente Abierta (secreto) | 88 |
| prudente | Ciudad Informada | 77 |
| impulsivo | Mandato Prestado | 84 |
| casual | Caos Informativo | 77 |
| dividido | Ciudad Dividida | 76 |

**Final secreto:** solo lo alcanza el perfil investigador, que reúne todas las pistas. Los otros cuatro perfiles no lo desbloquean por accidente. Las pruebas de `Destinos` cubren sus condiciones.

**Minijuegos**, todos jugados en el motor con mando simulado:

| Minijuego | Victoria | Derrota/error | Control para continuar |
|---|---|---|---|
| Moderación Express | Sí (6 tarjetas) | Sí (3 vidas perdidas) | A |
| Caza-Rumores | S con intercepción automática | — | A |
| Rastreador | A, tras un error explicado | Error con 0 de 2 eslabones | A |
| Gran Viralización | — | Sin intervenir: se pierde en 15 de 15 semillas de historia (simulación) | A |
| Duelo de Frecuencias | S, 97 %, con pausa y reanudación | D (sin pulsar) y abandono desde la pausa | A |

**Reintentos y siguiente visitante:** cada partida de feria crea un jugador y un alias nuevos (`story/leaderboard.rpy`, al empezar la partida). En esta sesión no se probó a mano una secuencia de varios visitantes seguidos.

## 8. Estado por área

| Área | Estado |
|---|---|
| Voces | Suenan con el idioma en español: 63 de 87 líneas del recorrido con voz (el resto es narración, que no se dobla). **No escuchadas por una persona.** |
| Música | Sin cambios. **No escuchada por una persona.** |
| Web | Publicada y sana. No sirve `.env`, partidas, `tools/` ni `.git`. Estos cambios **no** están publicados. |
| Teléfono real | **No verificado.** Solo la variante táctil en PC (§3). |
| Mando | Eventos simulados: menús, diálogo (`{w}` y `{nw}`), 5 minijuegos, pausa del duelo y resultados. **Sin hardware real.** |
| QR | La captura de la pantalla final decodifica a `https://ac020907.github.io/pruebaslaboratorio/`. `/static/qr.png` en Render da 404 hasta un *Manual Deploy* (no afecta al juego). |
| Backend | `/api/health?db=1` OK. `/docs` 404. Sin CORS para orígenes ajenos. 142 pruebas. Los recorridos de QA no envían nada a producción. |

## 9. Veredicto: GO condicionado

No quedan P0/P1 conocidos. Los flujos obligatorios funcionan en el motor y las suites pasan. **No está validado al 100 %.** Faltan:

1. **Mando físico:** decisiones, los 5 minijuegos, la pausa del duelo con Start → A y la pantalla final.
2. **Teléfono real** (iPhone Safari y Android Chrome, en horizontal): carga, sonido tras el primer toque, duelo en Fácil con toques y Rastreador táctil.
3. **Escucha humana:** voces, música y la pista del duelo, incluida la calibración.
4. **Partida de feria cronometrada** con personas (meta: 9–13 min).
5. **5 sesiones** de `PROTOCOLO_PRUEBAS_JUGADORES.md`. La planilla está lista; no se inventan resultados.

## 10. Artefactos de build

Build web publicada: `game.zip` **7.766.681 B** (antes 10,7 MB), sha256 `dd5f5748878399cf…`. No contiene partidas, QA, `docs/`, `tools/`, `tests/`, `leaderboard/` ni `.md`.

## 11. Git y despliegue

- **Cambios de esta auditoría:** commit `178e4db` en `qa/auditoria-final`, fusionado en `main` (`aae3248`) y publicado en `gh-pages` (`bb1cc1c`).
- **Para publicar** (cuando lo apruebes): commit en la rama, merge a `main`, *Manual Deploy* en Render, build web (`DESPLIEGUE.md` §3–4) y copia a `gh-pages`.
- **Rollback:**
  - Web: revertir el último commit de `gh-pages`.
  - Código: `git revert -m 1 <merge>`.
  - El backend no cambia en esta auditoría (sin cambios de esquema ni de API).

---

# Anexo: release anterior (Duelo de Frecuencias, publicada)

- **Rama:** `feature/duelo-frecuencias`, fusionada en `main` (merge `5279ad1`).
- **Punto de retorno:** tag `rc-estable-pre-ritmo` (versión anterior).
- **Fecha:** 2026-11-05.
- **Estado: publicada.**
  - **Web:** GitHub Pages (`gh-pages` `a958de0`) sirve esta versión en `https://ac020907.github.io/pruebaslaboratorio/`. Arranca y llega al menú.
  - **Servidor:** Render responde `{"ok":true,"db":"ok"}`. Falta un *Manual Deploy* de `main` en Render para servir `/static/qr.png` (hoy 404). El juego no depende de ese archivo: el QR va dentro de la build web.

## 1. Qué cambió

### Duelo de Frecuencias (quinto reto, original)
- **Motor puro:** `game/clases/Ritmo.py`. Incluye validación de charts, juez con ventanas configurables (Perfecto ±45 ms, Bien ±90 ms, Justo ±135 ms), combo, precisión, nota y la máquina de estados `countdown → playing ⇄ paused → results/aborted`.
- **Reloj de canción:**
  - usa la **posición real del audio** (`renpy.music.get_pos`);
  - extrapola entre los bloques del motor de audio;
  - usa el reloj de pared si el audio no informa nunca, por ejemplo en algunos navegadores;
  - no retrocede ni salta al reanudar.
- **Pantalla:** `game/minijuegos/ritmo.rpy`.
  - **Interfaz:** 4 carriles con forma propia (círculo, rombo, triángulo, cuadrado), de modo que no dependen del color.
  - **Personajes:** NOVA y el aliado del domingo reaccionan a combos y fallos.
  - **Indicador:** muestra señal frente a interferencia, con texto y porcentaje.
  - **Flujo:** cuenta atrás, pausa real que congela el audio, abandono seguro y resultados.
- **Dificultades:**
  - **Normal.**
  - **Fácil:** solo pulsos enteros y sin acordes; es la opción por defecto en pantallas táctiles.
  - **Asistido:** ventanas más amplias y meta del 45 %.
- **Calibración:** de ±200 ms, y velocidad visual de 0,75, 1 o 1,25, guardadas en el equipo.
- **Música original:** `tools/musica/duelo.py` genera `duelo_historia.ogg` (72 s) y `duelo_feria.ogg` (36 s) a 120 BPM, con llamada (NOVA) y respuesta (la señal de Ciudad Nova). Los **charts se derivan de los mismos eventos que suenan**: `game/ritmo/*.json`, 98 y 69 notas en historia, 43 y 29 en feria.
- **Nada de Friday Night Funkin':** no se copió música, sprites, charts, iconos ni código. Solo se tomó como referencia la mecánica observable: carriles, juicio por tiempo y llamada y respuesta.

### Narrativa e integración
- **Escena nueva:** `duelo_transmision` (en `story/elecciones.rpy`). El domingo, NOVA secuestra la transmisión oficial antes de la Gran Viralización. Se juega en historia y en feria.
- **Si ganas:** hecho `duelo_ganado`, consecuencias en la ciudad y **+1500 de umbral** en la Gran Viralización (`BONO_DUELO` en `story/rutas.rpy`). Se anuncia en pantalla.
- **Si pierdes:** hecho `duelo_perdido` y un impacto leve. No bloquea ningún final.
- **Los cinco finales no cambian de requisitos:** el duelo es un factor más.

### Puntuación y leaderboard
- **Escala intacta:** la Puntuación Cívica sigue en 0–1000. El componente "minijuegos" mantiene su máximo de 200 y ahora se reparte entre 5 retos.
- **Backend sin cambios de contrato:** las 142 pruebas pasan. Solo cambió la prueba del QR, que ahora acepta que el QR exista.
- **Datos ya publicados:** siguen siendo válidos.

### Correcciones de esta fase
- **Recorridos de QA contra producción:** en esta copia existe `game/leaderboard_url.txt`, así que los recorridos enviaban partidas al servidor de producción. Ahora QA nunca usa el servidor salvo con `--api`. Las 10 partidas de prueba ya enviadas están marcadas como **no verificadas**: no aparecen en la tabla pública. Ver §5.
- **Prueba del backend** que fallaba porque ya existe el QR.

## 2. Matriz de verificación

| Elemento | Implementado | Probado automáticamente | Probado visualmente | Escuchado | Hardware real |
|---|---|---|---|---|---|
| Motor rítmico (juicio, reloj, pausa, FPS) | Sí | 21 pruebas | — | — | — |
| Charts válidos y sincronizados con el audio | Sí | Sí: notas en la rejilla de 125 ms, duración ±60 ms, ataque de la señal a +10/+30 ms de la nota | — | **No** | — |
| Duelo dentro del motor real (feria 43 notas, historia 98) | Sí | Sí: 100 % Perfecto con el jugador automático, ningún cuadro de más de 20 ms | Sí: capturas de cuenta atrás, juego y resultados | **No** | — |
| Entrada con teclado (D F J K) | Sí | Eventos simulados: 43 de 43 | — | — | **No** |
| Entrada con mando (cruceta, X A Y RB, Start) | Sí | Eventos simulados: 43 de 43 | — | — | **No** |
| Táctil (tocar el carril, botón Pausa) | Sí | — | — | — | **No** |
| Web (Safari y Chrome móvil) | Respaldo del reloj si no hay posición | Respaldo con prueba unitaria | — | — | **No** |
| Cinco finales con el duelo | Sí | 10 de 10 recorridos | — | — | — |
| Lint de Ren'Py | — | Sin errores | — | — | — |
| Lógica, finales y backend | — | 37, 19 y 142 OK | — | — | — |

## 3. Pendiente (pruebas humanas y de hardware)
1. **Escuchar** `duelo_feria.ogg` y jugarlo una vez en PC. Si las notas se sienten adelantadas o atrasadas, ajusta la calibración en la pausa del duelo.
2. **Mando físico:** el duelo, las decisiones (prioridad heredada) y el resto de retos.
3. **Teléfono real:** el duelo en Fácil con toques, el sonido en iOS después del primer toque y la pausa.
4. **Partida de feria cronometrada:** la estimación es de unos 12 min (~80 líneas, 5 retos), pero no se ha medido con personas.
5. **Pendientes de fases anteriores:** escuchar voces y música, y las sesiones de `PROTOCOLO_PRUEBAS_JUGADORES.md`.

## 4. Cómo se promovió (y cómo repetirlo)
1. Fusiona la rama:
   ```bash
   git switch main && git merge --no-ff feature/duelo-frecuencias && git push origin main
   ```
   Render se redespliega desde `main`.
2. Comprueba el servidor:
   ```bash
   curl https://civitas-leaderboard.onrender.com/api/health?db=1
   ```
   Debe responder `{"ok":true,"db":"ok"}`.
3. Genera y publica la build web (`DESPLIEGUE.md` §3–4): `web_build`, luego `postbuild.py`, y copia sobre la carpeta de la rama `gh-pages` con `git add -A`, `git commit` y `git push`.
4. Abre `https://ac020907.github.io/pruebaslaboratorio/`, juega el duelo y confirma que la partida aparece en la tabla.
5. **Rollback:**
   ```bash
   git switch main && git revert -m 1 <commit del merge> && git push
   ```
   En `gh-pages`, revierte el último commit.

## 5. Limpieza opcional de las partidas de prueba en Neon
Las 10 partidas de QA (2026-11-05, hacia las 17:20 UTC) son no verificadas y no salen en la tabla pública. Si quieres borrarlas, en el *SQL Editor* de Neon revisa primero:
```sql
SELECT run_id, alias, score, created_at FROM scores
WHERE verified = false AND created_at BETWEEN '2026-11-05 17:00:00+00' AND '2026-11-05 17:40:00+00';
```
Si salen exactamente esas partidas de prueba, bórralas con la misma condición:
```sql
DELETE FROM scores
WHERE verified = false AND created_at BETWEEN '2026-11-05 17:00:00+00' AND '2026-11-05 17:40:00+00';
```

## 6. Créditos y licencias
- La música, los efectos y los sprites del duelo (formas de notas) son originales, generados con las herramientas del repositorio (`tools/musica`).
- Las voces usan TTS de Windows (OneCore).
- Las fuentes son Roboto (Apache 2.0).
- No se usaron recursos de terceros sin licencia.
