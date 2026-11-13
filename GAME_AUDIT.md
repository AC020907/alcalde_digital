# Auditoría y remasterización — Alcalde Digital

Fecha: 2026-10-17 · Motor: Ren'Py 8.5.3 · Resolución: 1920×1080
Respaldo previo a los cambios: `C:\Users\ALEJANDRO\Alcalde-Digital-respaldo-2026-10-17` (copia completa sin `.git`, saves ni caché).

## 1. Estado encontrado (antes de la remasterización)

| Área | Hallazgo | Severidad |
|---|---|---|
| Flujo | `script.rpy` dejaba al jugador esperando notificaciones por temporizador (`sistema_civitas`) dentro de un `while`; la narrativa se reducía a una intro de 5 líneas. | Crítica |
| Bug | El timer `Jump("evaluar_final")` de `sistema_civitas` cortaba la última publicación al vaciarse el banco. | Crítica |
| Bug | `script.rpy:37` usaba `%` sin escapar (aviso de lint). | Baja |
| Narrativa | Sin personajes con personalidad ni diálogos; los `Character` definidos (`inf`, `may`, `inv`, `ci`) no se usaban. | Alta |
| Arte | Un solo sprite (`inf_serious.png`) con relleno de piel sin terminar y 3 recoloreados; sin expresiones. `main_menu.png` era un rectángulo rosa plano. | Alta |
| UI | GUI por defecto de Ren'Py (gris, inglés), HUD como tira de 8 números. | Alta |
| Audio | Ningún archivo de audio. | Alta |
| Minijuegos | Rastreador, Contención y Viralización funcionales (versión arcade de la sesión anterior); Moderador solo como estructura. | Media |
| Código muerto | `story/randomEvents.rpy` con un `label event1:` vacío. | Baja |
| Recursos de otros devs | Arte valioso solo en la rama `origin/implementacion-mapa` (mapa ilustrado 6144×4096, pantalla de título ilustrada, iconos de rol). | — |

## 2. Principios de presentación aplicados (referencia: DDLC, sin copiar recursos)

- Caja de diálogo ancha y translúcida, pestaña de nombre flotante con color por personaje, indicador de continuar animado.
- Personaje que habla iluminado; el resto atenuado (función de foco en ATL), respiración sutil, reacciones breves (salto, temblor, sobresalto).
- Transiciones con nombre y duración consistente (`rapido` 0.15 s, `suave` 0.45 s, `negro` fade, `destello`).
- Música por estado de ánimo y silencio deliberado antes del clímax (cierre de urnas en negro).
- Un único momento que rompe el patrón (aparición de NOVA con interferencia), sin meta-horror ni manipulación de archivos.
- Elecciones con consecuencia visible inmediata: números flotantes sobre indicadores y avisos "X recordará esto".

Nota: no existe un postmortem técnico público detallado de DDLC; los valores son puntos de partida ajustados sobre la documentación oficial de Ren'Py.

## 3. Dirección artística

- **Mundo real** (escenas narrativas): ilustración cálida y pastel tomada de la pantalla de título y del mapa del equipo. Paleta crema `#fbf6ee`, tinta `#2b2440`, violeta `#5b5bd6`, lavanda `#a7a5f2`, coral `#e86a7e`, vino `#8c2f4b`.
- **Civitas** (teléfono y minijuegos): interfaz oscura con neón. El contraste es intencional: la red social es "otro mundo".
- Tipografía Roboto (Apache 2.0) en toda la interfaz.

## 4. Estructura actual

```
game/
├── script.rpy              flujo: prólogo → actos 1-3 → elecciones → finales
├── objects.rpy             banco AVL de 10 publicaciones + nueva_publicacion (teléfono)
├── screens.rpy             HUD, números flotantes, diálogo, elecciones, menú principal, opciones
├── story/
│   ├── personajes.rpy      elenco, expresiones, foco del hablante, reacciones, afinidad
│   ├── escenas.rpy         fondos, cámara, tarjetas de lugar, títulos de acto, interferencia
│   ├── sistema_narrativo.rpy  reintentos de minijuegos, comentarios de personajes, intro
│   ├── telefono.rpy        pantalla de Civitas para responder publicaciones
│   ├── prologo.rpy  acto1.rpy  acto2.rpy  acto3.rpy  elecciones.rpy
│   ├── finales.rpy         3 finales + epílogos por afinidad + pantalla de resultados
│   └── modo_feria.rpy      versión de ~6 minutos
├── minijuegos/             Moderador, Caza-Rumores, Rastreador, Gran Viralización, sustentación
├── clases/                 estructuras de datos (AVL, árbol N-ario, grafo, BFS/DFS, cola FIFO)
├── images/bg, images/personajes, gui/, fonts/, assets/audio/{music,sfx}
```

## 5. Sistemas de juego

- **Indicadores** (existentes, reutilizados): Confianza, Desinformación, Credibilidad (reputación del jugador) y Estabilidad (convivencia y conflictos), más información verificada y bienestar.
- **Relaciones**: `afinidad` con Claudia, Martina y Rodrigo; cambian con decisiones y resultados de minijuegos, y alteran epílogos y la ayuda en el clímax.
- **Finales**: Ciudad Informada, Ciudad Dividida y Caos Informativo (también por derrota inmediata), más el final secreto **Fuente Abierta** (sección 8). Se recuerdan en `persistent.finales_vistos`.
- **Minijuegos** integrados en la historia, con un reintento y consecuencias aplicadas solo al resultado final:
  1. Moderación Express (lunes, comentarios de Martina) — cola FIFO, tiempo real.
  2. Caza-Rumores (miércoles, Barrio Sur) — BFS en tiempo real.
  3. Rastreador (viernes, origen del rumor): **puzzle de tablero de evidencias** (arrastrar, clic o teclado). El jugador reconstruye la cadena origen → difusión → publicación viral, elige una conclusión y, en modo historia, infiere de dónde salió la captura viral (una publicación real recortada). Recibe explicaciones específicas por eslabón ("X publicó después de Y", "Z no sigue a W") y pistas en dos niveles (−5 s: fuentes posibles; −15 s: la cuenta). El caso se genera con BFS y se valida con DFS inverso; las pistas usan DFS restringido al tablero (`clases/PuzzleEvidencias.py`, `minijuegos/rastreador.rpy`). Historia: 3 eslabones, 3 señuelos, 120 s e inferencia. Feria: 2 eslabones, 2 señuelos, 75 s. La versión arcade anterior queda como `minijuego_rastreador_vivo` en el laboratorio.
  4. La Gran Viralización (domingo) — BFS acelerado; la afinidad puede facilitarlo.
- **Modo feria** (objetivo ~8 min, sin medir con personas): incluye los 4 minijuegos (Moderación, Caza-Rumores, Rastreador corto, Gran Viralización), CivitasNet, expediente, consecuencias diferidas, el giro de NOVA y el final secreto.

## 6. Arte integrado

- **Sprites transparentes** (desde 2026-10-19): `images/personajes/sprites/<nombre>_<expresion>.png`, 30 PNG (5 personajes × 6 expresiones) a resolución nativa (~550 px de alto). Los escala Ren'Py. Los genera `revision_visual/procesar_sprites.py` a partir de las hojas 3×2 del paquete:
  - limpia el canal alfa: quita el ruido menor que 14 y lleva el 252–253 a opaco;
  - separa las figuras con cortes por costura de costo mínimo, para no rebanar el cabello que toca a la figura vecina;
  - elimina las motas sueltas y el "!" flotante de NOVA "seria";
  - usa un lienzo común por personaje, alineado por el **centro de la cara** (piel o visor de NOVA) y la línea inferior. Entre las seis expresiones la cara no se mueve más de 1 px.
- **Puesta en escena** (`story/personajes.rpy`):
  - Los bustos se apoyan detrás de la caja de diálogo con un fundido inferior (`gui/fundido_busto.png`), así el corte del pecho nunca se ve y la cara queda sobre el texto.
  - `escena(tag, x, escala)` usa el centro del personaje: solo 0.5; dos personajes 0.28 y 0.72; tres personajes 0.17, 0.5 y 0.83 con escala 0.84.
  - Quien no habla se atenúa y retrocede un 3 %. La entrada es un fundido con subida corta; la respiración es sutil y se desactiva con "Reducir movimiento".
  - Hay luz de escena según el fondo: fría de noche y en la red de NOVA, cálida al atardecer.
  - Las expresiones cambiadas por atributo de diálogo se funden (`config.say_attribute_transition`).
  - El escalado y la línea base de cada personaje están en `ENCUADRE_SPRITE`; NOVA es más bajito a propósito.
- **Retratos laterales de diálogo:** `images/personajes/sprites/lado/` (30), recortados de los sprites.
- **Respaldos y CivitasNet:** se conservan los paneles anteriores (`images/personajes/<nombre>_<expresion>.png`), los retratos históricos `images/personajes/lateral/*_lado.png` (CivitasNet sigue usándolos) y los circulares `*_base.png`.
- **Fondos:**
  - `bg despacho` (prólogo);
  - `bg estudio_martina` (Acto 1 y feria);
  - `bg operaciones` (decisión del Acto 2, tablero del Acto 3, domingo y puzzle);
  - `bg redaccion` (Acto 3 y feria);
  - `bg barrio_sur conversacion`: el mapa aéreo desenfocado, para que Rodrigo no hable delante de un mapa nítido.
- **Revisión visual** (solo desarrollo): laboratorio (Shift+L) → "QA - Revisión visual de sprites, encuadres y fondos". Muestra las 6 expresiones de cada personaje, composiciones de 1, 2 y 3 personajes sobre 7 fondos, y aparición, cambio y salida.
- **Capturas** antes y después, láminas de control e informe del recorte: `revision_visual/` (fuera de `game/`, no entra en la build).

## 7. Riesgos y pendientes (arte)

| Prioridad | Pendiente |
|---|---|
| Media | No hay un fondo de calle del Barrio Sur: se usa el mapa aéreo desenfocado. Un fondo a nivel de calle mejoraría las escenas de Rodrigo. |
| Media | Los sprites son bustos de ~550 px y se muestran a 1,32×. En monitores 1080p se ven correctos; para 4K harían falta originales de mayor resolución. |
| Baja | En dos hojas (Claudia neutral y enojada) unos pocos píxeles de pelo llegan al borde de la hoja original; en pantalla quedan fuera del encuadre. |
| Baja | En el arte, Tomás aparece con traje y emblema de alcaldía; en la historia es el candidato rival. Se mantuvo la narrativa. |

## 8. Investigación narrativa (CivitasNet, expediente, NOVA y final secreto)

**Premisa:** NOVA no inventa los rumores. Toma una publicación real e incompleta de una fuente en la que la ciudad confía, la recorta y la repite. Detrás está Resonancia Consultores, que programa las cuentas (panel RSN-Scheduler) y vende la "solución" una hora después de cada crisis.

### Archivos

| Archivo | Rol |
|---|---|
| `clases/Investigacion.py` | Catálogos inmutables (publicaciones, fichas, eventos, IDs de hechos) y consultas puras. |
| `story/investigacion.rpy` | Estado de partida (`default memoria`, `default final_secreto`), `hecho()`, `dar_pista()`, efectos de minijuegos y del teléfono. |
| `story/civitasnet.rpy` | Pantalla CivitasNet (HUD o `call abrir_civitasnet(id)`). |
| `story/expediente.rpy` | Pantalla del expediente. |
| `story/novagiro.rpy` | `giro_nova`, `giro_nova_tardio`, `revision_expediente`, `final_fuente_abierta`. |
| `story/eventos_variables.rpy` | Eventos variables y sus escenas. |
| `tests/test_civitas_logica.py` | 27 pruebas de lógica pura con semillas fijas. |

**Estado:** `memoria` es la única fuente de verdad y es serializable (dict/list/str/int). Guarda `momento`, `hechos`, `pistas` (id → estado), `eventos` y `semilla`. `mem()` completa claves en partidas antiguas. CivitasNet y el expediente derivan todo de `memoria`; las pantallas no guardan estado propio. `hecho()` rechaza IDs que no estén en `inv.HECHOS`. El rollback sigue desactivado (decisión previa, para que retroceder no duplique consecuencias).

### Mapa de interdependencias

| Publicación / fuente | Pista | Elección | Consecuencia inmediata | Consecuencia diferida |
|---|---|---|---|---|
| `net_veneno` y `net_memo_salud` (prólogo, 06:09 y 06:02) | `captura_veneno`, `memo_salud_nova` | Desmentir ya / pedir análisis / ignorar | Comunicado en CivitasNet; reacción de Claudia | Miércoles: "NOS MINTIERON" o el informe del Acueducto; saludo distinto de Rodrigo; NOVA usa (o no) el desmentido en el giro |
| Comentarios de Martina | — | Moderación (minijuego) | Post de Martina: desmentido o "#MartinaCensura" | Línea de Claudia esa noche; ayuda de Martina en la Gran Viralización (feria) |
| Teléfono (banco AVL) | — | Compartir una falsa / verificar / reportar | Titular de @noticias.nova o nota del editor | Tomás reacciona el domingo si compartiste una acusación |
| Anuncios de Resonancia (lunes y miércoles) | `anuncio_resonancia` | Inspeccionar en CivitasNet | Ficha en el expediente | Nueva pregunta a NOVA; opción "Resonancia" en la revisión final |
| Rodrigo (miércoles) | `testimonio_acueducto` | Preguntar por el agua | Ficha | Prueba para el final secreto |
| Rastreador | `panel_programacion`, `captura_recortada` | Resolver la cadena y la inferencia | Post "rastreamos el rumor"; NOVA "me encontraste" | Prueba para el final secreto; refuta la hipótesis inicial |
| Revisión del expediente (domingo) | `conclusion_resonancia` | Quién está detrás y cómo publicarlo | — | Final secreto **Fuente Abierta** |

### Final secreto: condición exacta

Se cumple con `final_secreto` en verdadero e `inv.final_secreto_disponible(memoria)`:

- una pista de cada grupo de `PISTAS_CLAVE`:
  - rastreador: `panel_programacion`;
  - civitasnet: `anuncio_resonancia`;
  - diálogo o consecuencia: `testimonio_acueducto` o `informe_acueducto`;
- y en `revision_expediente`, elegir "Resonancia Consultores" y "Publicar el expediente completo, con fuentes".

Filtrarlo de forma anónima no lo desbloquea. Ningún evento variable es necesario para el final secreto. La pantalla de resultados muestra "Expediente: N de 3 evidencias decisivas", sin nombrarlas.

### Eventos variables

Son seis, uno como máximo por momento, y se eligen en `preparar_partida()`:

- cuenta secundaria;
- filtración a Martina;
- foto de 2019;
- video verificable;
- rectificación de @salud.nova;
- captura falsa de la alcaldía.

La feria solo usa variantes cortas. Para QA:

- `ALCALDE_SEMILLA=123` fija la semilla;
- `ALCALDE_EVENTOS="1:cuenta_secundaria,2:ninguno,4:captura_falsa"` fuerza eventos (momentos: 1 lunes, 2 miércoles, 3 viernes, 4 domingo);
- el laboratorio (Shift+L en el menú, solo en modo desarrollador) muestra la semilla y los eventos.

### Pruebas ejecutadas (2026-10-18)

- **Lint de Ren'Py:** sin errores.
- **Lógica pura:** `python tests/test_civitas_logica.py` → 27 pruebas OK.
- **Recorridos automáticos en el motor:** con un arnés temporal ya eliminado; los minijuegos de acción se jugaron de forma automática.
  - Historia, perfil prudente: final "Dividida".
  - Historia, perfil impulsivo: final "Dividida", y el giro usa su desmentido.
  - Historia, perfil investigador: final secreto, con todos los eventos forzados.
  - Historia, perfil casual: pierde el puzzle; NOVA habla el domingo en CivitasNet; final "Caos".
  - Modo feria, investigador: final secreto.
  - Modo feria, casual: final "Dividida".
  - Reinicio desde el menú: estado limpio.
  - Guardado en CivitasNet (miércoles) y carga en otra ejecución: estado, pistas y eventos restaurados; llega al final.
  - Carga de una partida guardada con la versión anterior (`auto-1`): funciona, sin las decisiones previas a la actualización.
- **No probado:** arrastre con ratón real, duración del modo feria con personas, comprensión del giro por jugadores. Ver `PROTOCOLO_PRUEBAS_JUGADORES.md`.

## 9. Riesgos y pendientes

| Prioridad | Pendiente |
|---|---|
| Media | Sprites con transparencia (figura recortada) si se quiere un estilo de VN clásico; hoy son paneles enmarcados. |
| Media | Audio sintetizado de forma procedural: verificado numéricamente (sin saturación, bucles continuos) y se reproduce sin errores dentro del juego, pero **nadie lo ha escuchado todavía**; necesita una escucha del equipo. |
| Alta | Prueba con 3 a 5 jugadores que no conozcan el proyecto (protocolo en `PROTOCOLO_PRUEBAS_JUGADORES.md`): duración real del modo feria, comprensión del puzzle y del giro. **Pendiente.** |
| Media | Arrastrar fichas del puzzle con ratón real (el arrastre se probó llamando al mismo callback; clic y teclado sí se probaron en el motor). |
| Baja | En el arte, Tomás aparece con traje y emblema de alcaldía; en la historia es el candidato rival. Se mantuvo la narrativa. |
| Baja | Multijugador (fuera del alcance de esta entrega). |

## 10. Remaster narrativo y de plataforma (2026-11-04)

Pedido de la profesora: historia más atractiva, voces, mejor música y un ritmo menos precipitado. El equipo añadió: consecuencias reales, mando, versión web y clasificación online.

### Historia y rutas
- **Volumen:** de 210 a 373 bloques de diálogo y de 17 a 29 decisiones.
- **Escenas nuevas de calma e investigación:**
  - Tomás en la plaza (lunes).
  - La confesión de Claudia sobre 2019 (lunes por la noche).
  - La tienda de Rodrigo (miércoles).
  - La oferta de Resonancia a Martina (miércoles por la noche).
  - El audio falso de Tomás (viernes).
  - La víspera con una persona a elegir (sábado).
- **Arcos conectados:** la familia de la foto de 2019 es la de Rodrigo. Si el jugador une las piezas, Claudia y Rodrigo se encuentran el miércoles y él puede mediar.
- **Consecuencias intermedias:**
  - La oferta a Martina decide si el domingo ella ayuda o promociona a Resonancia. Exponerla da una evidencia alternativa del final secreto: `oferta_resonancia`.
  - El audio de Tomás abre o cierra "Mandato Prestado" y bloquea el final secreto si se usó.
  - El sábado y las alianzas deciden quién ayuda en la Gran Viralización y cambian su dificultad (`UMBRAL_ALIADO` en `story/rutas.rpy`).
- **Cinco finales** con escena, música y personajes propios (`clases/Destinos.py`): Ciudad Informada, Ciudad Dividida, Caos Informativo, **Mandato Prestado** (nuevo) y Fuente Abierta. Los epílogos dependen de las rutas.

### Puntuación Cívica y clasificación
- **Puntuación** (`clases/Puntuacion.py`, 0–1000): verificación 300, decisiones 250, minijuegos 200, investigación 150 y ciudad 100. El final no garantiza el máximo.
- **Clasificación online:** backend en `leaderboard/` (93 pruebas). El cliente está en `story/leaderboard.rpy`: alias anónimo, cola de envíos pendientes y nunca bloquea la partida.
- **Archivo de Destinos:** los finales como coleccionables.

### Voces y música
- **Voces:** 301 líneas dobladas con TTS de Windows (`tools/voces/`): Claudia, Martina, Rodrigo, Tomás y NOVA, con voz procesada.
  - Ren'Py las reproduce con `config.auto_voice` y baja la música mientras alguien habla.
  - Narrador y jugador no tienen voz, como en las novelas visuales clásicas.
- **Música:** 14 temas y 10 efectos nuevos, compuestos de forma procedural (`tools/musica/`). Hay un leitmotiv de Ciudad Nova y otro de NOVA. El sistema `musica()` está en `story/rutas.rpy`.
- **Aviso:** voces y música se verificaron numéricamente (sonoridad, picos, bucles, espectrogramas), pero **nadie las ha escuchado todavía**.

### Mando, móvil y web
- **Mando** (`story/mando.rpy`): acciones comunes para teclado y gamepad.
  - Mapa, Moderador y arcade (mira virtual) funcionan con cruceta y botones.
  - En el Rastreador, la cruceta mueve el foco entre fichas y huecos, y A elige y coloca.
  - Y no oculta la interfaz, porque congelaba los minijuegos.
- **Móvil:**
  - Flechas táctiles en el mapa, botón "Llegar" e "Ir directo".
  - Texto un 20 % más grande en teléfonos.
  - En la web se oculta "Salir" y en vertical aparece un aviso de girar el teléfono.
- **Build web:** exportada con el módulo oficial de Ren'Py 8.5.3 (101 MB en total, 47,7 MB de descarga inicial; imágenes, música y voces se descargan bajo demanda). Pasos en `DESPLIEGUE.md`.

### Pruebas ejecutadas
| Prueba | Resultado |
|---|---|
| Lint de Ren'Py | Sin errores |
| `tests/test_civitas_logica.py` | 37 OK |
| `tests/test_destinos_puntuacion.py` | 19 OK |
| `leaderboard` (pytest) | 93 OK |
| `tests/qa_recorridos.py` (guion real en el motor, 5 perfiles × historia y feria) | 10/10 llegan a su final esperado |
| Envío real juego → servidor local | Aceptado, rechazo por duración imposible, sin servidor (queda en cola) y reconexión (reenvío) |
| Web en navegador | Arranca, reproduce el prólogo, descarga las voces y consulta la clasificación con CORS |
| Mando (eventos simulados con `controller.post_event`) | Mapa, Moderador, Caza-Rumores y Rastreador responden |
| Capturas reales del motor | Escritorio y variante móvil (`RENPY_VARIANT`) revisadas |

**No probado:** mando físico, iPhone y Android reales, escucha humana de voces y música, y despliegue en Render y GitHub Pages (requiere las cuentas del equipo).
**QA reproducible:** `python tests/qa_recorridos.py [--api URL]`. Aparta `game/saves` mientras corre, para no tocar el progreso real.

## 11. Pulido final y QA para la feria (2026-11-04)

### Doblaje
- **Auditoría objetiva** con `tools/voces/auditar_voces.py`. Transcribe cada línea con un reconocedor offline en español (Vosk) y mide WER, silencios, saturación y sonoridad. El resultado queda en `tools/voces/auditoria_voces.csv`.
- **Problemas encontrados y corregidos:**
  - 108 de 301 líneas tenían silencios internos de más de 1 s, porque OneCore cierra cada bloque de prosodia con una pausa larga. Ahora las pausas se comprimen a un máximo natural por personaje, y quedan **0 líneas** con más de 1 s.
  - "Civitas" se acentuaba "ci-VI-tas": ahora es "Cívitas".
  - "RSN-Scheduler" era ininteligible.
  - Se doblaban 11 líneas de herramientas de desarrollo, entre ellas "Reacción de temblor"; ya no.
- **Resultado:** 298 líneas. WER mediano 0 en Claudia, Martina, Rodrigo y Tomás, y 0,09 en NOVA (voz procesada). Ninguna saturación.
- **Pendiente:** la escucha humana. El reconocedor no detecta voces monótonas, poco emotivas o con acento poco natural. Las 133 líneas de las escenas clave están priorizadas para grabación humana en `tools/voces/GRABACION_RECOMENDADA.md`.

### Música y sonido
- Los sonidos de interfaz usan los efectos nuevos: hover, confirmación de decisiones y pista nueva.
- **Mezcla inicial:** música 0,7, efectos 0,8 y voz 1,0, con atenuación de la música mientras se habla.
- Los 14 temas pasan la verificación de sonoridad, picos y bucles.
- **Pendiente:** la escucha humana.

### Narrativa
- Se eliminó la redundancia de Claudia sobre por qué aceptó ayudar: en el balcón ahora revela que "no era toda la verdad".
- En feria, Claudia se presenta y hay transiciones entre días.
- La ayuda del aliado del domingo, o el perjuicio del video de Martina, se anuncia en pantalla.
- **Duración medida por recorrido** (no estimada):

| Modo | Líneas | Palabras | Voz |
|---|---|---|---|
| Feria | 71–82 | ~1.000 | ~5 min |
| Historia | 153–190 | 2.000–2.550 | 9–12,5 min |

  Con los minijuegos, la feria dura unos 10–12 min. El botón ahora dice "Modo Feria (10 min)".

### Mando (eventos simulados, sin hardware)
**Funciona:**
- Menú principal: la cruceta mueve el foco.
- El diálogo avanza con A.
- El teléfono de Civitas completo funciona con cruceta y A.
- CivitasNet y el expediente se cierran con B.
- El Archivo de Destinos y la clasificación se cierran con A.
- Mapa, Moderador, Caza-Rumores y Rastreador funcionan, incluida la colocación de fichas con A.
- Corregido: Y ya no congela minijuegos.

**Sin confirmar:** en el menú de elecciones, el ratón inyectado funciona, pero el teclado y el mando inyectados no. Todo apunta a un artefacto de la inyección (es el menú estándar de Ren'Py), pero **no se pudo verificar** con teclado real ni con mando. Se añadió foco inicial en la primera opción. Es la **prueba manual prioritaria**.

### Web
- Descarga inicial reducida de 59 a 47,7 MB:
  - la música pasa a carga progresiva;
  - se excluyen 30 paneles de personaje sin uso, los placeholders y el sprite de influencer.
- La build no incluye partidas guardadas, herramientas ni documentos.
- La build anterior se probó en el navegador (arranque, voces, clasificación con CORS). **La build optimizada final no se pudo abrir**, porque el panel del navegador no estaba disponible: hay que probarla.

### Leaderboard
Auditoría y endurecimiento: 142 pruebas. Ver la sección "Seguridad" de `leaderboard/README.md`.
- La tabla pública solo muestra partidas verificadas, con duración medida por el servidor y umbrales mayores para puntuaciones altas.
- Hay límites por jugador.
- Se corrigieron falsos rechazos a jugadores honestos.
- En producción el CORS solo admite GitHub Pages.
- Cada partida de feria cuenta como un visitante nuevo.

### Pruebas manuales pendientes (antes de la feria)
1. **Mando físico:** menú de elecciones (cruceta + A), los cuatro minijuegos, mapa, pausa (Start) y pantalla final.
2. **Teléfono real** (iPhone Safari y Android Chrome, en horizontal): carga, sonido tras el primer toque, Rastreador táctil, mapa táctil y final.
3. **Escucha** de voces (empezando por `GRABACION_RECOMENDADA.md`) y de la música en cada escena.
4. **Partida completa** contra Render + Neon reales.
5. **Sesiones** con 5 jugadores nuevos según `PROTOCOLO_PRUEBAS_JUGADORES.md`.

## 12. Auditoría final con capturas del motor real (2026-11-05)

**Método:** `tests/qa_visual.py` fotografía el juego real.
- **Recorridos:** el guion completo de los 5 perfiles, una captura por línea.
- **Galería por etapas** (`game/qa_galeria.rpy`): menús, escenas, teléfono, CivitasNet, expediente, mapa, los 5 minijuegos jugados con entradas de mando simuladas (victoria, derrota, error y abandono) y las 5 pantallas de final.
- **Detalle:** el detalle por defecto y las rutas de las capturas están en `RELEASE_READINESS.md`.

| P | Defecto | Causa raíz | Corrección |
|---|---|---|---|
| P0 | El Duelo de Frecuencias se congelaba tras pausar y pulsar CONTINUAR. Las notas quedaban quietas y el duelo se perdía. | `VistaDuelo` solo pide cuadros desde `render()` mientras se juega. Al reanudar, nadie pedía el primero. | `renpy.redraw` al reanudar y al abandonar. Verificado: pausa y reanudación con mando dan S, 97 %. |
| P1 | Moderación: con mando, A no salía de la pantalla de resultados. | Al terminar seguían visibles la tarjeta y BORRAR/APROBAR, y el foco podía quedar en ellos. | Se ocultan al terminar, `civ_accion` continúa y el botón usa el estilo del juego. |
| P2 | En el tutorial y la pausa del duelo, los botones y el texto se salían del panel. | Tres `boton_vn` (406 px) no caben en 1068 px. | Estilo `boton_vn_compacto` (300 px, `Frame`) y panel de pausa de 1040 px. |
| P2 | Guardar, Cargar, Ayuda y las confirmaciones salían en inglés ("Page 1", "empty slot", "Upload Sync", toda la ayuda). | El proyecto no tenía traducción de los textos del motor. | `game/tl/spanish` (traducción oficial del SDK), `config.language = "spanish"` y Sync desactivado. Las voces siguen sonando: 63 de 87 líneas con voz en el recorrido; el resto es narración. |
| P2 | El rótulo del mapa "BARRIO SUR" quedaba detrás de Rodrigo en la conversación. | Las vistas aéreas traen el rótulo pintado. | El plano de conversación encuadra una zona del barrio sin rótulos. El inpainting se descartó porque dejaba una mancha. |
| P2 | Textos visibles sin tildes: publicaciones de CivitasNet, avisos de alcance, narración de la red, avisos y motivos de fin de los arcades y del rastreo, "Versión" y "LA GRAN VIRALIZACIÓN". | Textos escritos sin acentos. | 47 líneas corregidas solo en cadenas visibles, sin tocar claves de diccionario. La narración no tiene voz, así que no se rompe ningún archivo de voz. |
| P3 | Las notas del duelo pasaban por encima del título y la barra de señal. Al abandonar quedaban notas congeladas detrás del resultado. | Se dibujaban desde y = −60 y también en resultados. | Las notas nacen bajo la cabecera con un fundido y no se dibujan en resultados. |
| P3 | 3,8 MB de PNG opacos en la descarga inicial web (fondos de menú). | `main_menu.png` y `game_menu.png` sin transparencia. | JPG: de 3,05 MB a 0,68 MB y de 0,74 MB a 0,07 MB. |
| P3 | El botón EMPEZAR del Rastreador usaba el estilo por defecto (azul) sobre un panel claro. | — | Usa `boton_vn`. |

**Comprobado y sin defecto:**
- **Los 5 finales** se alcanzan con renderizado real: secreto, informada, mandato, caos y dividida.
- **El QR** de la pantalla final se decodifica desde la captura a `https://ac020907.github.io/pruebaslaboratorio/`.
- **Mando:** A avanza la narración, las líneas de personaje, las pausas `{w}` del prólogo y las líneas `{nw}`. El historial registra las líneas.
- **Gran Viralización sin intervenir** se pierde: 0/15 semillas en historia y 1/15 en feria.
- **La web publicada** no sirve `.env`, partidas, herramientas ni `.git`. El backend responde con la base de datos OK, `/docs` está cerrado y no hay CORS para orígenes ajenos.

**Artefactos del arnés de QA, no del juego:**
- **Historial y menú:** el QA arranca dentro del `splashscreen`, donde Ren'Py desactiva historial y menú del juego. La galería los restaura.
- **Texto animado:** la primera A completa la línea y la segunda avanza, que es lo esperado. Las capturas usan texto instantáneo.
- **Ventana:** pedir 1920×1080 en ventana da 1739×978, porque Windows reserva la barra de tareas. Es la misma proporción 16:9.
