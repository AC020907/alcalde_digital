## AYUDA (rubrica §16): objetivo, reglas, botones, personajes/roles, como ganar e indicadores.
## Se abre desde el menu principal, desde el menu del juego (Esc / B) y desde la Arena.

init python:
    AYUDA_PESTANAS = (("objetivo", "Objetivo y cómo ganar"), ("reglas", "Reglas"), ("arena", "Arena (2-4 jugadores)"),
                      ("personajes", "Personajes y roles"), ("indicadores", "Indicadores"), ("botones", "Botones y controles"),
                      ("accesibilidad", "Accesibilidad"))

screen ayuda_civitas(pestana="objetivo"):
    modal True
    zorder 150
    default actual = pestana
    key "game_menu" action Hide("ayuda_civitas")
    add Solid("#120d1ce6")
    frame:
        style "arena_panel"
        align (0.5, 0.5)
        xysize (1760, 980)
        hbox:
            spacing 30
            vbox:
                xsize 380
                spacing 8
                text "AYUDA" style "arena_titulo"
                for clave, titulo in AYUDA_PESTANAS:
                    textbutton titulo:
                        style "arena_opcion"
                        text_style "arena_opcion_texto"
                        selected (actual == clave)
                        selected_background Frame("gui/boton_menu_hover.png", 34, 24)
                        action SetScreenVariable("actual", clave)
                        default_focus (clave == actual)
                null height 10
                textbutton "Cerrar" style "boton_vn_compacto" text_style "boton_vn_text" action Hide("ayuda_civitas")
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                xsize 1270
                vbox:
                    spacing 14
                    xsize 1230
                    use expression "ayuda_" + actual

style ayuda_h is default:
    size 28
    bold True
    color "#8c2f4b"
style ayuda_p is default:
    size 22
    color "#2b2440"

screen ayuda_objetivo():
    text "Objetivo" style "ayuda_h"
    text "Ciudad Nova elige alcalde y en la red social Civitas circulan noticias verdaderas, opiniones y rumores falsos. Tu objetivo es que la ciudad termine las elecciones con la mayor información verificada, convivencia, confianza, bienestar digital y participación responsable, y con la menor desinformación, conflicto y cantidad de rumores." style "ayuda_p"
    text "Cómo se gana" style "ayuda_h"
    text "· Historia y Modo Feria: no hay un único final bueno. Tus decisiones, pistas y retos llevan a uno de cinco destinos (Ciudad Informada, Dividida, Caos Informativo, Mandato Prestado o el final secreto Fuente Abierta) y a una Puntuación Cívica de 0 a 1000." style "ayuda_p"
    text "· Arena (2-4 jugadores): cada jugador suma una puntuación individual y la ciudad obtiene un resultado común. Al final, los ciudadanos votan entre los cuatro candidatos según la confianza que dejaron vuestras decisiones. Gana la partida quien más puntos tiene; la ciudad gana si su índice cívico supera 65." style "ayuda_p"
    text "El juego no hace preguntas de examen: aprendes viendo qué pasa en la ciudad con cada cosa que compartes, verificas, ignoras o reportas." style "ayuda_p"

screen ayuda_reglas():
    text "Cada publicación" style "ayuda_h"
    text "Puedes Compartir, Verificar, Ignorar o Reportar. Verificar te muestra lo que encuentras sobre la fuente y te pregunta si es verdadera: si lo es, la compartes con la fuente; si no, la reportas." style "ayuda_p"
    text "Lo que compartes se propaga por la red social: cuanto más conectada esté una cuenta, más lejos llega. Lo que reportas deja de llegar a quienes te siguen." style "ayuda_p"
    text "Tiempo limitado" style "ayuda_h"
    text "Algunas decisiones tienen cuenta atrás. Si no decides a tiempo, la publicación sigue corriendo sin ti y pierdes participación." style "ayuda_p"
    text "Azar" style "ayuda_h"
    text "Cada partida trae eventos distintos (una noticia falsa, algo que se vuelve viral, una discusión, una campaña de convivencia…). El azar decide qué aparece; tú decides qué hacer con ello." style "ayuda_p"
    text "Historia" style "ayuda_h"
    text "Recorre Ciudad Nova en el mapa, habla con Claudia, Martina, Rodrigo y Tomás, reúne pistas en el Expediente, revisa CivitasNet y supera cinco retos distintos: Moderación Express, Caza-Rumores, Rastreador, Duelo de Frecuencias y, en la Gran Viralización del domingo, la Ruta de la Verdad: un plataformas en el que entras al sistema de NOVA a rescatar la evidencia (A/D o flechas para moverte, Espacio para saltar)." style "ayuda_p"

screen ayuda_arena():
    text "Arena Civitas: multijugador local" style "ayuda_h"
    text "1. Todos en la misma red (wifi o cable). Un equipo elige «Crear sala»: ese equipo es el servidor y muestra su IP." style "ayuda_p"
    text "2. Los demás eligen «Unirse», escriben esa IP, un nombre y un rol libre. Hacen falta de 2 a 4 jugadores; cada rol solo puede elegirlo uno." style "ayuda_p"
    text "3. Cuando todos marcan «Listo», el anfitrión pulsa «Empezar». Hay 5 rondas. En cada una aparece una publicación y todos deciden a la vez, contra el reloj." style "ayuda_p"
    text "4. El servidor junta las decisiones, propaga la publicación por el grafo social de Ciudad Nova, cambia los indicadores y reparte puntos. Verás quién la recibió, quién quedó protegido y por qué." style "ayuda_p"
    text "5. Al terminar se vota alcalde entre Tomás Vega, Juan Ortega, Inés Prado y Elena Ruiz. El resultado explica qué decisiones movieron los votos." style "ayuda_p"
    text "Torneo: Consejo Cívico + 5 pruebas" style "ayuda_h"
    text "En «Torneo completo» (5 rondas) o «Torneo Feria» (2 rondas y pruebas más cortas), al acabar el Consejo cada uno juega en su equipo los minijuegos de la historia, con la misma semilla para todos: Moderación Express, Rastreador, Caza-Rumores, Ruta de la Verdad (plataformas) y, como final, el Duelo de Frecuencias (PERFECT, GREAT, GOOD, MISS)." style "ayuda_p"
    text "Cada prueba vale de 0 a 1000 y el Consejo de 0 a 2000; el servidor recalcula todo a partir de tus decisiones. La media del grupo en cada prueba mejora o empeora Ciudad Nova antes de votar: el campeón del torneo y el resultado de la ciudad son cosas distintas. Si no entregas a tiempo o te desconectas, esa prueba cuenta 0." style "ayuda_p"
    text "Arena Online (teléfonos o computadores en redes distintas)" style "ayuda_h"
    text "1. Abre la Arena Online (botón en el menú de la Arena, o en la versión web). 2. Una persona pulsa «Crear sala» y comparte el código de 5 letras o el enlace de invitación. 3. Las demás escriben el código, eligen un rol libre y pulsan «Estoy listo». 4. Si alguien recarga la página o pierde la señal, al volver a abrir el enlace sigue en su puesto." style "ayuda_p"
    text "La Arena Online es una historia compartida en 5 rondas. En cada una: una escena común, una pista que solo ve tu rol, un reto que juegan todos (Moderación, Rastreador, Caza-Rumores, Ruta de la Verdad y, como gran final, el Duelo de Frecuencias), los resultados y una decisión cívica sobre lo que circula en Civitas. Al final se muestran el campeón del torneo, el alcalde elegido y cómo quedó Ciudad Nova." style "ayuda_p"
    text "El servidor da la salida a la vez y comprueba cada resultado. En el Duelo hay que pulsar «Entrar al duelo» para activar el sonido. Para el público hay una pantalla de espectadores (enlace en la sala) que no muestra las pistas privadas." style "ayuda_p"
    text "Si alguien pierde la conexión durante la partida, su puesto se guarda y la ronda sigue sin él; con «Reconectar» vuelve a su mismo puesto. El anfitrión puede pausar una ronda y añadir jugadores automáticos si falta gente." style "ayuda_p"

screen ayuda_personajes():
    text "Roles de la Arena" style "ayuda_h"
    for r in AR.ROLES:
        text "%s: %s" % (AR.NOMBRE_ROL[r], AR.DESCRIPCION_ROL[r]) style "ayuda_p"
    text "El influencer gana y pierde el doble de puntos porque sus decisiones llegan más lejos. El periodista ve la fuente real al verificar; los demás solo una pista. El candidato defiende a Inés Prado." style "ayuda_p"
    text "Personajes de la historia" style "ayuda_h"
    text "Tú: alcalde de Ciudad Nova durante la semana electoral." style "ayuda_p"
    text "Claudia Reyes: periodista de Noticias Nova; te ayuda a investigar el origen de los rumores." style "ayuda_p"
    text "Martina: influencer con mucho alcance; lo que publique puede apagar o encender un rumor." style "ayuda_p"
    text "Rodrigo: vecino del Barrio Sur; representa a la ciudadanía y sus miedos." style "ayuda_p"
    text "Tomás Vega: candidato rival; puede ser aliado si se juega limpio." style "ayuda_p"
    text "NOVA: la red de cuentas automáticas que fabrica y empuja rumores." style "ayuda_p"

screen ayuda_indicadores():
    text "Indicadores de Ciudad Nova" style "ayuda_h"
    text "Suben con decisiones responsables (conviene que estén altos):" style "ayuda_p"
    for k in ("info_verificada", "confianza", "convivencia", "bienestar", "participacion"):
        text "· %s: %s" % (AR.NOMBRE_INDICADOR[k], {"info_verificada": "noticias comprobadas que llegaron a la gente.",
            "confianza": "cuánto se creen los ciudadanos entre sí y en sus instituciones.",
            "convivencia": "si se puede discutir sin insultos ni bandos.",
            "bienestar": "cansancio y miedo que deja la red; baja con conflictos y rumores.",
            "participacion": "ciudadanos que actúan y votan informados; decide la abstención."}[k]) style "ayuda_p"
    text "Suben con decisiones irresponsables (conviene que estén bajos):" style "ayuda_p"
    for k in AR.NEGATIVOS:
        text "· %s: %s" % (AR.NOMBRE_INDICADOR[k], {"desinformacion": "falsedades que la gente cree.",
            "conflictos": "peleas y ataques entre vecinos o campañas.",
            "rumores": "historias sin confirmar que siguen circulando."}[k]) style "ayuda_p"
    text "En la historia el HUD muestra Confianza, Desinformación, Credibilidad (tu reputación) y Estabilidad (convivencia y bienestar)." style "ayuda_p"

screen ayuda_botones():
    text "Ratón y pantalla táctil" style "ayuda_h"
    text "Clic o toque: avanzar el diálogo y elegir. Rueda: historial. En la Arena, toca cada opción del árbol; «« Volver» regresa a la opción anterior." style "ayuda_p"
    text "Teclado" style "ayuda_h"
    text "Enter o Espacio: avanzar y aceptar. Flechas: moverse entre opciones y conducir en el mapa. Esc: menú del juego (guardar, opciones, ayuda). H: pista en el Rastreador. En el Duelo: D F J K. En la Ruta de la Verdad: A/D o flechas y Espacio para saltar (mantén para saltar más alto)." style "ayuda_p"
    text "Mando" style "ayuda_h"
    text "A: aceptar. B: menú / cerrar. Cruceta o palanca: moverse y elegir. X: onda (Caza-Rumores). Y: pista. LB: volver un paso. Start: pausa." style "ayuda_p"
    text "Botones de la pantalla" style "ayuda_h"
    text "Ciudad, CivitasNet, Expediente, Misiones y Mapa (arriba a la derecha) abren cada panel. En la Arena, el anfitrión tiene «Empezar», «Pausar ronda», «Siguiente ronda» y «Añadir jugador automático»." style "ayuda_p"

screen ayuda_accesibilidad():
    text "Pensado para más personas" style "ayuda_h"
    text "· Subtítulos: todo lo que se dice por voz aparece siempre escrito, también con el sonido apagado." style "ayuda_p"
    text "· Avisos visuales de sonido (Opciones → Accesibilidad): cada efecto importante (alarma viral, pista, logro, error) aparece también como un aviso escrito, para jugar sin audio o con pérdida auditiva." style "ayuda_p"
    text "· Reducir movimiento: quita paneos y animaciones de cámara para quien se marea." style "ayuda_p"
    text "· Nada depende solo del color: las notas del Duelo tienen forma propia y los indicadores llevan nombre y número." style "ayuda_p"
    text "· Velocidad del texto y avance automático regulables, y dificultad Fácil/Asistido en el Duelo." style "ayuda_p"
