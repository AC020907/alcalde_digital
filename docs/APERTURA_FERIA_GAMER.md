# Apertura «Ciudad Nova en crisis» (Feria Gamer)

## Por qué se cambió

La profesora pidió un inicio mucho más dinámico e impactante para los jurados. Había gustado el multijugador y los minijuegos, pero el comienzo era lento y no estaba a su altura.

| Inicio anterior (Modo Feria, contado en el guion) | Ahora |
|---|---|
| 7 líneas de diálogo (447 caracteres) y la pantalla de CivitasNet antes de la primera decisión | 15 s de montaje sin texto que leer y 2 líneas de Claudia: decisión a los ~22 s |
| El primer minijuego llegaba tras 26 líneas (≥ 1.745 caracteres), el teléfono, CivitasNet y varios menús | Microprueba jugable a los ~45 s |
| La consecuencia era un número flotante | La consecuencia se ve en el mapa de la ciudad: el BFS real de tu respuesta, con los indicadores animados |

## Guía de dirección artística de la apertura

| Aspecto | Decisión |
|---|---|
| **Estilo** | Se respetan las ilustraciones planas del equipo: no se añaden 3D, realismo, brillos, partículas ni neón. La profundidad sale de la cámara, el encuadre y el ritmo. Lo dibujado en código (red, logo) usa el mismo lenguaje que el lineart de los sprites: **trazo de tinta oscura y color plano encima**, círculos con contorno y ningún degradado. |
| **Paleta** | Tinta `#2b2440`, papel `#fbf6ee`, noche `#120d1c` y lila `#c9b8d8` para textos secundarios. Un solo color de emergencia, `#d1495b` (el rumor), y su opuesto `#3d7ea6` (lo que tu respuesta frena). Vino `#8c2f4b` para rótulos. Es la paleta de la interfaz y la ropa de Claudia: no se introduce ningún color nuevo. |
| **Luz** | No hay efectos de luz. El amanecer se cuenta con una veladura nocturna que se retira (3 s), y el silencio del primer plano, con una veladura que vuelve. |
| **Cámara** | Solo tiene tres funciones: **avanzar** (amanecer, 9 s lineal), **seguir la información** (el mapa se abre a medida que el rumor llena la ciudad y baja hasta la Alcaldía) y **acercarse en una línea clave** («Y ayer... esa cuenta no existía», `camera at ap_acercar`). Nunca se mueve mientras se lee una tarjeta. |
| **Transiciones** | Cada transición une dos acontecimientos:<br>• la notificación crece hasta ser la publicación (corte por movimiento);<br>• la publicación se hunde en el barrio donde nació el rumor;<br>• el mapa baja hasta el edificio de la Alcaldía y abre el despacho;<br>• el teléfono de Claudia se convierte en la pantalla de moderación.<br>Las entradas y salidas duran 0,3–0,6 s y los movimientos de cámara, 6–9 s. |
| **Tipografía** | Roboto Light espaciada para la marca y los rótulos de lugar («CIUDAD NOVA», «ALCALDE DIGITAL»). Roboto en negrita, sin espaciar, para lo que hay que leer rápido. Sin mayúsculas gigantes que entren y salgan. |
| **CivitasNet** | Tarjetas de papel con una franja de color a la izquierda y la cuenta en vino. Son las mismas en las notificaciones, el teléfono de la decisión y la transición a la moderación. |
| **Ritmo** | Calma (0–3 s, solo ciudad y música suave), incertidumbre (3–6 s, 1 → 3 notificaciones), **silencio** (6,3 s, la música se corta en el primer plano), crisis (8,2 s, tensión y alarma, el rumor se propaga), despacho (diálogo breve), decisión (sin música nueva), consecuencia, acción y título (transición sonora y tema «revelación»). |
| **Personajes** | No se deforma ningún sprite. Claudia entra con un desplazamiento lateral corto (0,5 s) y cambia de expresión con cada línea; la cámara se acerca en el momento clave. Durante la decisión sigue en escena, a la derecha. |
| **Título** | Logo propio: **cada letra de CIVITAS es un nodo**. Una arista llega, el punto se marca y la letra sube; el primer punto es rojo, el origen del rumor. Debajo, «ALCALDE DIGITAL» espaciado en rojo y el lema. Sirve igual para el tráiler, el stand o las diapositivas (`TituloRed`). |
| **NOVA** | Su interferencia aparece una sola vez (0,5 s, franjas), justo cuando Claudia dice que la cuenta no existía ayer. |

## El flujo (`game/story/prologo.rpy` + `game/story/apertura.rpy`)

| # | Escena | Implementación |
|---|---|---|
| 1 | **Ciudad Nova antes del caos.** Panorama al amanecer con un avance lento de cámara, y el rótulo «CIUDAD NOVA · lunes 6:09». | `screen apertura_montaje`, `ap_plano_ciudad` |
| 2 | **El rumor se propaga.** 1 notificación, después 3. La publicación pasa a primer plano en silencio y se hunde en el mapa. El rumor corre de cuenta en cuenta (BFS real), con un contador y dos viñetas de vecinos reaccionando. La cámara se abre sobre la ciudad y baja a la Alcaldía. Dura ~15 s; clic, Enter o «Saltar». | `CiudadRumor` + ATL |
| 3 | **El despacho.** Del edificio de la Alcaldía al interior, con el plano abriéndose. Claudia entra: 2 líneas en Feria y 3 en Historia. | `ap_revela_despacho`, `ap_entra_lado` |
| 4 | **La decisión.** El teléfono con la publicación a la izquierda y Claudia a la derecha, sin salir de la escena. Tres respuestas («Responder como alcalde») y «Ver de dónde salió» (pista `captura_veneno`). Ninguna opción aparece marcada como la buena. | `menu (screen="apertura_decision")`, un menú real: el guardado, el rollback y la QA lo respetan |
| 5 | **La consecuencia.** El mapa de nuevo, con el BFS de tu respuesta: alcance, cuentas frenadas en azul, barras de confianza, desinformación e información verificada que se mueven del valor anterior al nuevo, y la reacción de un ciudadano. | `screen apertura_reaccion` |
| — | **Claudia reacciona a tu elección** (sin repetirla) y trae la pista: la cuenta no existía ayer. | `prologo.rpy` |
| 6 | **Primer desafío.** El teléfono de Claudia llena la pantalla y se convierte en Moderación Express: 4 comentarios. | `apertura_a_moderacion` + `ColaModeracion` / `moderador_ui` |
| 7 | **Título.** | `screen apertura_titulo`, `TituloRed` |
| — | Estilo del alcalde y Acto I. | sin cambios |

## Estructuras de datos que intervienen

- **Grafo dirigido y ponderado** (`red_civitas`): las escenas 2 y 5 dibujan un **BFS real** (`bfs_propagacion`: cola FIFO, conjunto de visitados y padres) desde `@verdad.oculta`, con semilla fija. Cada cuenta está en su barrio del mapa (`MAPA_ZONAS`, espiral de Fermat por barrio) y cada arista es el padre BFS real. La respuesta cambia el recorrido:
  - **desmentir:** bloquea a quienes siguen a la alcaldía;
  - **pedir análisis:** bloquea a los medios;
  - **no intervenir:** sin bloqueos y con propagación ×1,35.

  Alcance sobre 27 cuentas: 16, 17 y 24.
- **Cola FIFO** (`ColaModeracion`): la microprueba.
- **Diccionarios de estado:** `apertura_decision`, `apertura_antes` (indicadores antes de decidir, para animar las barras), `apertura_micro` y `apertura_tiempos`.

## Consecuencias conservadas, aplicadas una sola vez

| Respuesta | Indicadores (los mismos de antes) | Marcas |
|---|---|---|
| Desmentir | confianza +2, información verificada −2 | `desmintio_sin_datos`, calidad 0,4 |
| Pedir análisis | información verificada +3, desinformación +2 | `pidio_analisis`, calidad 1,0, Claudia +1 |
| No intervenir | desinformación +4, confianza −2 | `ignoro_rumor_agua`, calidad 0,0, Claudia −1 |

- `apertura_decidir()` no se aplica dos veces, y después de decidir se bloquea el rollback.
- La microprueba aplica un efecto pequeño una sola vez y no toca `registro_minijuegos`.
- Sus 4 comentarios no están en el banco del Moderación Express completo (una prueba lo verifica).
- La cuenta atrás de la moderación ya no dice «Martina» en la microprueba: el texto es `moderacion_intro`, y se restaura para el reto del lunes.
- Se conservan la pista `hip_nova_creo`, las escenas posteriores que leen las marcas, la elección de estilo y los cinco finales.

## Rendimiento y accesibilidad

- **Precarga:** el menú principal precarga el panorama, el mapa (3072 px), el despacho y los recortes de barrio (`renpy.start_predict`). Sin esto, el primer inicio tardaba ~5 s en mostrar el montaje; con la precarga, el montaje arranca al instante, comprobado en la ventana real.
- **Dibujo:** `CiudadRumor` dibuja 28 nodos y sus aristas con el canvas de Ren'Py sobre una sola textura de mapa y deja de redibujarse al terminar. Es compatible con Ren'Py Web (no usa hilos ni extensiones).
- **Reducir movimiento:**
  - la cámara corta entre posiciones en vez de moverse;
  - no hay desplazamientos ni zoom en las entradas;
  - la propagación aparece por niveles, sin crecer;
  - el título aparece completo.

  El montaje dura lo mismo para que se pueda leer.
- **Control y avisos:** todo se puede **saltar o acelerar** con clic, Enter, el botón «Saltar» o el mando (`civ_accion`). Los sonidos tienen aviso visual (`sfx`) y no hay flashes. Las voces se doblaron con ElevenLabs (19 líneas nuevas o reordenadas de Claudia en total); la del jugador no se dobla, por diseño.

## Demostración ante profesores y jurados (≈ 1 min 15 s)

1. **Menú → «Modo Feria (12 min)».** Dejar correr el montaje: ciudad, notificaciones, silencio y el rumor en el mapa.
2. **Despacho:** dos líneas de Claudia.
3. **Decisión:** pulsar «Ver de dónde salió» y elegir una respuesta.
4. **Consecuencia:** el mapa muestra a quién llegó el rumor según tu respuesta. Las cuentas azules son las que frenaste, y las barras se mueven. Para comparar, repetir con «No intervenir» (24 cuentas) o «Desmentir» (16).
5. **Microprueba:** borrar los 2 bots y aprobar a las 2 personas, una de ellas crítica.
6. **Título** y paso natural al Lunes.

## Pruebas realizadas (2026-11-12)

| Prueba | Resultado |
|---|---|
| `renpy.exe . lint` | Sin errores |
| `python -m pytest -q tests` | **190 OK**, incluidas las 8 de `tests/test_apertura.py` |
| `python tests/qa_recorridos.py` | **10/10**: los 5 finales en Historia y en Feria, pasando por la nueva decisión |
| `qa_visual.py galeria --etapas apertura` | OK con desmentir, analizar y no intervenir; en Historia; con reducir movimiento. Indicadores, pistas, afinidad y marcas correctos y aplicados una vez |
| Partida real en la ventana (ratón y teclado; flechas en la microprueba) | Montaje → despacho → decisión → consecuencia → pista → microprueba (4/4) → título → estilo, sin errores |

**Correcciones hechas tras revisar capturas y la ventana real:**
- la cámara se salía del borde del mapa: ahora se limita a sus bordes;
- el grafo se leía débil sobre la ilustración: trazo y nodos más gruesos, y veladura más oscura;
- el contador tapaba «Barrio Norte»;
- el panel de la consecuencia tapaba Prensa: ahora va abajo a la derecha, sobre el mar;
- la barra sin cambio salía roja: ahora es neutra;
- los números flotantes duplicaban el panel;
- había espacio vacío en el teléfono de la decisión;
- el menú rápido aparecía sobre la decisión;
- la cuenta atrás de la microprueba decía «Martina»;
- el fondo del título competía con «ALCALDE DIGITAL»;
- había ~5 s de carga al primer inicio.

**Medición simulada** (lector automático de ~15 caracteres/s que deja correr el montaje completo; **no son datos de personas**):

| Hito | Feria | Historia |
|---|---|---|
| Primer acontecimiento (la ciudad; notificación a los 3,2 s) | < 1 s | < 1 s |
| Fin del montaje (crisis comprendida) | 15,7 s | 15,7 s |
| Decisión disponible | 22,2 s | 23,5 s |
| Decisión y consecuencia visible | 27,4 s | 28,7 s |
| Microprueba | 44,7 s | 46,0 s |
| Título | 63,7 s | 65,0 s |
| Fin del prólogo | 79,3 s | 80,6 s |

Saltando el montaje, la decisión llega en ~7 s.

**Capturas reales del motor** en `docs/auditoria/apertura/`:
- `serie_montaje_1s.jpg`: una captura por segundo del montaje;
- `ap03`–`ap09`: decisión, consecuencia (con cada respuesta), Claudia, microprueba y título.

**Sin verificar:** mando físico (las acciones existen, pero no se probó con un mando conectado), la versión web (no se ha publicado esta rama) y las pruebas con personas (protocolo abajo).

## Protocolo de prueba con personas (pendiente: no se ha realizado)

Al menos **5 personas ajenas al equipo**. Una sesión por persona, sin explicar nada antes: solo «es un juego sobre una ciudad en elecciones».

1. Abre el juego en el menú y pídele que elija «Modo Feria». Cronometra desde ese clic.
2. No ayudes. Anota los tiempos y lo que diga en voz alta.
3. Detén la sesión en el título «CIVITAS» o al empezar el Lunes.

| Dato | Cómo registrarlo |
|---|---|
| ¿Le interesó en los primeros 5 s? | Observación: mira la pantalla, comenta, se inclina |
| Tiempo hasta comprender la crisis | Cuando diga, con sus palabras, que hay un rumor sobre el agua |
| Tiempo hasta la primera interacción | Primer clic o tecla con intención |
| ¿Comprendió su responsabilidad? | Pregunta al final: «¿Quién eras tú y qué tenías que hacer?» |
| ¿Entendió las consecuencias? | «¿Qué pasó en la ciudad por lo que elegiste?» |
| ¿Reconoce una identidad propia? | «¿Te recuerda a algún otro juego?» y «¿Qué imagen recuerdas?» |
| ¿Quiso seguir jugando? | «¿Quieres saber quién está detrás?» (sí, no o tal vez) |
| Momento que más llamó su atención y escena lenta | Preguntas abiertas |
| Problemas de controles o lectura | Observación directa |

Plantilla de registro (una fila por persona; no anotes nombres ni datos personales):

| # | Interés 5 s | Crisis (s) | 1.ª interacción (s) | Responsabilidad | Consecuencias | Quiere seguir | Lo mejor | Lo lento | Problemas |
|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | |
| 2 | | | | | | | | | |
| 3 | | | | | | | | | |
| 4 | | | | | | | | | |
| 5 | | | | | | | | | |

**Criterio orientativo:** al menos 4 de 5 comprenden la crisis durante el montaje, entienden que su respuesta cambió la propagación y quieren seguir.
