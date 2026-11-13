# Remasterización visual de Civitas

**Rama:** `feature/remaster-visual`. **Punto de recuperación:** tag `checkpoint-pre-remaster`. Sin push ni deploy.

La remasterización cambia **cómo se presenta** el juego, nunca **qué ocurre**. La historia, los diálogos, las decisiones, los finales y el arte oficial de los personajes están intactos, y se puede verificar (ver «Integridad»).

## 1. Integridad verificable

| Comprobación | Herramienta | Resultado |
|---|---|---|
| **Arte oficial** (`game/images/personajes/**`: sprites, laterales, bases; 155 archivos) | `python tools/remaster/inventario.py comparar docs/remaster/inventario_antes.json` (SHA-256) | **Idénticos**. Ningún PNG de personaje se sobrescribió; la presentación usa transforms |
| **Narrativa** (labels, diálogos, opciones con su condición, `call`/`jump` entre labels; 652 elementos en 41 archivos) | El mismo comando. El «antes» se generó desde el tag `checkpoint-pre-remaster` | **Idénticos** |
| **Diálogo oficial de Ren'Py** (identificador, personaje y texto de cada línea; enlaza las voces) | `renpy.exe . dialogue` comparado con `docs/remaster/dialogo_antes.tab` | **Sin diferencias** |
| **Los cinco finales y el secreto** | `python tests/qa_recorridos.py` | **10/10** en Historia y en Feria |

Mostrar una pantalla (`call screen`) se considera presentación y no entra en el inventario narrativo. Las nuevas cartelas de desenlace y el cierre son pantallas; no añaden texto a la historia.

## 2. Dirección artística unificada

La referencia son los sprites oficiales: dibujo plano, contorno definido, expresiones claras. Todo lo nuevo se dibuja con el mismo lenguaje.

| Elemento | Regla |
|---|---|
| **Trazo** | Contorno de tinta `#2b2440` y color plano encima. Nada de degradados, brillos, partículas decorativas ni neón. |
| **Paleta** | Tinta `#2b2440`, papel `#fbf6ee`, noche `#120d1c`, lila `#c9b8d8`, vino `#8c2f4b`. Rojo de emergencia `#d1495b` (rumor y peligro), teal `#2f9e8f` (red ciudadana y lo verificado), ámbar `#e8b04b` (evidencia). |
| **Componentes** | **Tarjeta de papel** con contorno de tinta y franja roja (CivitasNet). Se usa en notificaciones, el rótulo de lugar, el HUD del plataformero y los resultados de los minijuegos. |
| **Tipografía** | Roboto Light espaciada para la marca y los títulos (logo, cartelas, título del menú del juego). Roboto en negrita para lo que se lee rápido. |
| **Marca** | **La línea de red con nodos** del logo CIVITAS se repite: en las cartelas de acto (la semana de lunes a domingo, con el acto marcado), en la ruta del plataformero y en las cartelas de los desenlaces. |
| **Movimiento** | La cámara avanza, sigue o se acerca con intención. Las entradas duran 0,35–0,45 s. Con «reducir movimiento» no hay desplazamientos, sacudidas ni zooms. |

## 3. Auditoría y estado por pantalla

Clasificación: **P0** impide comprender o jugar · **P1** presentación grave · **P2** falta de pulido · **P3** opcional.

| Pantalla | Problema encontrado | Prioridad | Mejora aplicada | Evidencia | Estado |
|---|---|---|---|---|---|
| **Ruta de la Verdad: juego** | Bloques rectangulares genéricos, protagonista diminuto (~50 px), fondo de rascacielos neón genérico, HUD en barra negra | P1 | Tileset nuevo con **autotiling** (16 variantes × 2, contorno solo en los lados expuestos, sin costuras). **Parallax en 3 planos**: Ciudad Nova, del panorama oficial entintado; torres de NOVA con pantallas del rumor; cables en primer plano. **Avatar propio del minijuego** redibujado (~108 px, 14 cuadros). Barreras de interferencia animadas con franjas de aviso (forma, no solo color). Plataformas inestables que se agrietan y tiemblan antes de apagarse. **Documentos** como coleccionables. **Antenas** como punto de control, con onda. **Puerta del Archivo** como meta. Polvo y papeles con contorno. Squash al aterrizar, pose al recoger, sacudida y estática al ser detectado, pose de victoria. HUD en fichas de papel y **ruta como línea de red**. | `comparativas/plataformero_juego.jpg`, `capturas/j11_plataformas_juego_b.jpg` | Hecho |
| **Ruta de la Verdad: resultados** | Panel azul marino genérico | P1 | Tarjeta de papel: calificación en círculo, objetivo cumplido o pendiente, cuatro fichas de cifras y **cada documento recuperado con su nombre** | `comparativas/plataformero_resultado.jpg` | Hecho |
| **Ruta de la Verdad: tutorial** | Iconos antiguos | P2 | Iconos y fondo nuevos | `comparativas/plataformero_tutorial.jpg` | Hecho |
| **Moderación Express** | **El título salía cortado** («ÓN EXPRESS»): la cabecera centrada se desbordaba | **P0** | Cabecera reorganizada: título a la izquierda y marcadores a la derecha | `comparativas/moderacion_cabecera.jpg` | Hecho |
| **Resultados de Moderación, Caza-Rumores y Rastreador** | Tres estilos distintos (papel, azul marino, botones azules ajenos a la paleta) | P1 | Componente común `resultado_tarjeta` (`minijuegos/resultado_comun.rpy`), con los mismos textos y cifras de cada motor | `comparativas/moderacion_resultado.jpg`, `rastreador_resultado.jpg` | Hecho |
| **Escrutinio** | Panel estático con las cifras ya puestas | P1 | **Cuenta las cifras exactas del motor** (`Eleccion.escrutinio_historia`): mesas escrutadas 0 → 100 %, barras y votos que suben, «Contando votos…», el ganador revelado al cerrar el conteo y los «¿por qué?» uno a uno. Avatares: Tomás con su **lateral oficial sin modificar**; el resto, con iniciales. Fondo del mapa de la ciudad. | `comparativas/escrutinio.jpg`, `capturas/f01_escrutinio_conteo_informada.jpg` | Hecho |
| **Los cinco finales** | Misma presentación para todos | P1 | Cartela de desenlace (nombre, insignia y lema del Archivo de Destinos) e identidad por final (ver tabla 4) | `capturas/f0*_escena_*.jpg`, `f01_cartela_informada.jpg` | Hecho |
| **Cierre** | Del resultado se volvía al menú sin transición | P2 | Pantalla de cierre con el logo, tu destino, los destinos descubiertos y «Gracias por jugar» (6 s, se puede saltar). Se conserva el Archivo de Destinos. | `capturas/f01_cierre_informada.jpg` | Hecho |
| **Cartelas de acto** | Texto plano sobre negro | P2 | Identidad del logo: el mapa de la ciudad al fondo y la **línea de la semana** con el acto marcado | `comparativas/cartela_acto.jpg` | Hecho |
| **Rótulo de lugar** | Recuadro genérico pequeño | P2 | Tarjeta de CivitasNet con franja roja y el lugar en Roboto Light | `comparativas/rotulo_lugar.jpg` | Hecho |
| **Menú del juego** (Opciones, Guardar, Cargar, Historial, Ayuda, Créditos) | **El título salía cortado por arriba**; la veladura blanquecina parecía sin terminar; las ranuras vacías eran bloques grises | **P0** / P1 | Título visible en Roboto Light con acento rojo. Panel de papel sólido con la columna de navegación en lila y separador de tinta. Ranuras de guardado como tarjetas de papel con contorno. | `comparativas/menu_opciones.jpg`, `menu_guardar.jpg` | Hecho |
| **Prólogo** | — | — | Ya remasterizado (`docs/APERTURA_FERIA_GAMER.md`) | `docs/auditoria/apertura/` | Hecho (rama anterior) |
| **Duelo de Frecuencias** | Funciona y se ve bien | P3 | Sin cambios: no se tocaron ventanas, charts, música ni reglas | — | Sin cambios |
| **Caza-Rumores, propagación y Gran Viralización (juego)** | Fondo tecnológico neón genérico; barra superior azul marino | P2 | Fondo nuevo: **el mapa ilustrado de Ciudad Nova entintado** (`tools/arte/fondos_minijuegos.py`), así que el grafo se juega sobre la ciudad real. Barra superior en el color noche de la paleta. Los originales quedan en `tools/arte/respaldo_v1/`. | `capturas/j05_contencion_2_juego.jpg` | Hecho |
| **Rastreador (tablero)** | Explicación del error en rojo sobre la foto (poco legible); conclusión elegida con degradado | P1 | La explicación va en una tira de papel con franja roja (la etiqueta de la mesa se oculta mientras se muestra). Los botones de conclusión son planos: vino si está elegida y noche con contorno lila si está disponible. | `capturas/j14_rastreador_error.jpg` | Hecho |
| **HUD de la ciudad** (Ciudad, CivitasNet, Expediente, Misiones, Mapa) | Píldoras azul marino con degradado | P2 | Fichas de papel con contorno de tinta y franja roja al pasar el ratón; los avisos pendientes en un círculo rojo con contorno; el panel de la ciudad, enmarcado | `capturas/e03_barrio_conversacion.jpg` | Hecho |
| **CivitasNet, Expediente, Mapa, Misiones** | Coherentes entre sí; sin defectos P0 o P1 detectados | P3 | — | — | Sin cambios |
| **Escenas de la novela** (personajes) | — | — | Ya existían entrada con subida y fundido, respiración, foco que atenúa a quien no habla y reacciones (`funcion_foco`). Se añaden rótulos, cartelas, cámara en la apertura y en los finales. | — | Hecho |
| **Arena Local (LAN)** | — | — | Usa las mismas pantallas de Ren'Py que Historia y Feria, así que recibe el plataformero, los fondos y los resultados nuevos. La red y el protocolo no cambian. | — | Hecho |
| **Arena Online (navegador)** | Plataformero con el arte antiguo; fondos neón | P1 | **Mismo arte que Ren'Py** en WebP: 58 archivos, 128 KB (`tools/arte/exportar_plataformas_web.py`). Se reescribió solo `dibujarPlat` en `static/arena.html`: autotiling, 3 planos, avatar con poses, squash, documentos que flotan, antenas con onda, archivo, partículas con contorno, sacudida y estática al ser detectado, HUD en fichas, `prefers-reduced-motion`. Fondos de los retos de grafo reexportados. **`plat_motor.js` (física) no cambia**: las pruebas de paridad Python/JS pasan. | E2E con Chrome: 2 navegadores, 5 retos, exit 0 | Hecho (requiere deploy en Render) |

## 4. Identidad de cada desenlace

Todo es presentación añadida a las escenas existentes (`story/finales_cine.rpy`); los diálogos no cambian.

| Final | Color | Cámara | Capa | Sensación |
|---|---|---|---|---|
| Ciudad Informada | Tinte cálido, +brillo | Se abre y sube hacia el cielo (9 s) | — | Esperanza, recuperación |
| Ciudad Dividida | Desaturado (0,55) | Fija | **Grieta** que parte la imagen y mitades teñidas de teal y vino | Fragmentación |
| Caos Informativo | Rojo apagado | **Cámara en mano** (desvíos irregulares) | **Publicaciones contradictorias** que se cruzan («GANÓ VEGA», «FRAUDE en la mesa 14»…) | Saturación |
| Mandato Prestado | Frío, muy desaturado | **Se cierra** sobre el poder (14 s) | **Bandas de cine** que estrechan el encuadre | Ambigüedad, encierro |
| Fuente Abierta | Papel cálido | Se abre | **El expediente** se arma: RSN-Scheduler, Resonancia, el informe del Acueducto, @verdad.oculta, unidos con hilo rojo | Revelación |

## 5. Recursos nuevos

- `game/gui/plataformas/v2/` (58 PNG), generados con `tools/arte/plataformas_arte.py`. Es el archivo editable: los parámetros de forma y color están en el código y se regeneran con un comando.
  - Si se quiere mantener el tamaño en disco de la distribución, los PNG antiguos de `gui/plataformas/` se pueden excluir del build; no se borraron.
- `gui/button/slot_*_background.png` y `gui/overlay/game_menu.png`, rehechos.
- No se usó material de terceros. El fondo lejano del plataformero es el panorama oficial del juego, entintado.

## 6. Rendimiento

| Medida | Antes | Después |
|---|---|---|
| Plataformero (QA de minijuegos, RTX 4070, 1920×1080) | 178 FPS | 140–142 FPS |

Sigue muy por encima de 60.
- **Capas:** los fondos son dos texturas de 3840 px enlazables más una de cables.
- **Dibujo:** las partículas y la ruta se dibujan con un solo canvas por cuadro.
- **Visibilidad:** los tiles fuera de cámara no se dibujan.
- **Escrutinio y finales:** usan `AnimatedValue` y `DynamicDisplayable` con refresco limitado, y dejan de redibujarse al terminar.

## 7. Pruebas ejecutadas (2026-11-12)

| Prueba | Resultado |
|---|---|
| `renpy.exe . lint` | Sin errores (3 ejecuciones). Una ejecución intermedia reportó un error transitorio de lectura de `nova_seria.png`; el archivo estaba intacto (hash, git y PIL) y no se reprodujo |
| `python -m pytest -q tests` | **190 OK**: incluye la paridad del motor del plataformero Python/JS (motor sin cambios) |
| `cd leaderboard && python -m pytest -q` | **165 OK** (el backend no se tocó) |
| `python tests/qa_recorridos.py` | **10/10** finales |
| `qa_visual.py galeria --etapas minijuegos` | OK: los 5 minijuegos, con el plataformero completado (S, 5/5) |
| `qa_visual.py galeria --etapas finales` | OK: por cada final, cartela, escena con su identidad, escrutinio contando y revelado, resultados y cierre |
| `qa_visual.py galeria --etapas menus,escenas` | OK |
| `qa_visual.py galeria --etapas apertura` | OK |
| Inventario de arte y narrativa | **Idénticos** |

**Arena Online:** `python tests/e2e_arena_online.py --jugadores 2` contra el servidor local termina con exit 0 (5 retos, campeón y elección).

**Sin verificar:**
- partida completa con mando físico;
- versión web de esta rama (no se publicó);
- pruebas con personas.
