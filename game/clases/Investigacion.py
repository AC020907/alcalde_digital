"""
Contenido inmutable y logica pura de la investigacion: publicaciones de CivitasNet,
fichas del expediente, eventos variables y condiciones del final secreto.

El estado de partida vive en Ren'Py (default memoria, ver story/investigacion.rpy) y
tiene esta forma serializable:
    {"momento": int, "hechos": [str], "pistas": {id: estado}, "pistas_nuevas": [id],
     "posts_vistos": [id], "eventos": {momento: id | None}, "semilla": int}
Las funciones de este modulo solo leen ese dict; no guardan estado propio.
"""
import random

PROLOGO, LUNES, MIERCOLES, VIERNES, DOMINGO = range(5)
NOMBRE_MOMENTO = ["Lunes, 6 a.m.", "Lunes", "Miércoles", "Viernes", "Domingo"]

ESTADOS_POST = {
    "pendiente":   ("SIN VERIFICAR", "#8b84a8"),
    "cuestionada": ("CUESTIONADA", "#d97706"),
    "verificada":  ("VERIFICADA", "#2f9e8f"),
    "manipulada":  ("MANIPULADA", "#e04f5f"),
    "publicidad":  ("PUBLICIDAD", "#7c6fd6"),
}

ESTADOS_PISTA = {
    "observado":  ("Hecho observado", "#5b5bd6"),
    "hipotesis":  ("Hipótesis", "#d97706"),
    "comprobado": ("Conclusión comprobada", "#2f9e8f"),
    "refutado":   ("Hipótesis refutada", "#8b84a8"),
}

# Hechos narrativos validos (story/investigacion.rpy rechaza cualquier otro ID).
HECHOS = (
    # Prologo
    "desmintio_sin_datos", "pidio_analisis", "ignoro_rumor_agua", "informe_publicado",
    # Telefono (banco de publicaciones)
    "publico_sin_verificar", "acuso_sin_evidencia", "verifico_y_desmintio", "reporto_verdad",
    # Resultados de minijuegos
    "moderacion_limpia", "moderacion_fallida", "crisis_contenida", "crisis_desbordada",
    "rastreo_exitoso", "rastro_perdido", "viral_frenado", "viral_desbordado",
    # Decisiones y eventos
    "confio_claudia", "confio_martina", "confio_rodrigo", "martina_publico_filtracion",
    # NOVA y desenlace
    "nova_hablo", "giro_desmentido", "giro_medio", "giro_silencio", "expediente_publicado",
)

CATEGORIAS_PISTA = ["publicacion", "captura", "documento", "testimonio", "conexion"]
NOMBRE_CATEGORIA = {"publicacion": "Publicaciones", "captura": "Capturas", "documento": "Documentos",
                    "testimonio": "Testimonios", "conexion": "Conexiones"}


def _post(id, momento, orden, autor, tipo, hora, texto, estado="pendiente", fuente=None, contexto=None,
          pista=None, condicion=(), revelado=(), variantes=(), likes=0, reposts=0):
    return {"id": id, "momento": momento, "orden": orden, "autor": autor, "tipo": tipo, "hora": hora,
            "texto": texto, "estado": estado, "fuente": fuente, "contexto": contexto, "pista": pista,
            "condicion": tuple(condicion), "revelado": tuple(revelado), "variantes": tuple(variantes),
            "likes": likes, "reposts": reposts}


# ---------------------------------------------------------------------------
# CivitasNet: publicaciones escritas a mano. "condicion" usa tokens:
#   "hecho"  /  "!hecho"  /  "pista:id"  /  "!pista:id"  /  "evento:id"
# ---------------------------------------------------------------------------
PUBLICACIONES_NET = [
    # ----- Prologo -----
    _post("net_memo_salud", PROLOGO, 1, "@salud.nova", "medio", "06:02",
          "El Acueducto revisa la muestra 14 del Barrio Sur por turbidez. Repetirán el análisis hoy.",
          fuente="Captura de un memo interno del Acueducto",
          contexto="Cuenta verificada de un medio de salud. Fue la primera publicación sobre el agua: siete minutos antes que cualquier otra. Dice 'repetirán el análisis', no 'contaminada'.",
          pista="memo_salud_nova",
          revelado=((("pista:captura_recortada",), "verificada"), (("pista:rectificacion_salud",), "verificada"),
                    (("pista:informe_acueducto",), "verificada")),
          likes=312, reposts=41),
    _post("net_veneno", PROLOGO, 2, "@verdad.oculta", "bot", "06:09",
          "URGENTE: el Acueducto CONFIRMA que el agua de Ciudad Nova está contaminada. No la tomen. #AntesDeQueLoBorren",
          fuente="Una captura sin enlace ni fecha",
          contexto="La captura que adjunta tiene la misma tipografía que la publicación de @salud.nova, pero está cortada justo debajo del título. La cuenta no tiene foto ni historial.",
          pista="captura_veneno",
          revelado=((("pista:captura_recortada",), "manipulada"), (("rastreo_exitoso",), "manipulada")),
          likes=40210, reposts=18900),
    _post("net_alcaldia_desmiente", PROLOGO, 3, "@alcaldia.nova", "institucion", "07:05",
          "El agua de Ciudad Nova es 100% segura. No crean rumores.",
          estado="cuestionada", fuente="Comunicado oficial, sin análisis adjunto",
          contexto="La alcaldía lo publicó antes de tener los resultados del Acueducto. Ningún dato respalda el '100%'.",
          pista="declaracion_alcaldia", condicion=("desmintio_sin_datos",), likes=2100, reposts=640),
    _post("net_alcaldia_analisis", PROLOGO, 3, "@alcaldia.nova", "institucion", "07:05",
          "Pedimos al Acueducto los análisis completos de la muestra 14. Informaremos con datos hoy mismo.",
          fuente="Comunicado oficial", contexto="No afirma ni niega nada todavía: promete datos.",
          condicion=("pidio_analisis",), revelado=((("informe_publicado",), "verificada"),), likes=980, reposts=120),
    _post("net_vecina_silencio", PROLOGO, 3, "@vecina.ana", "ciudadano", "07:40",
          "¿Nadie de la alcaldía va a decir nada del agua? Mis hijos van al colegio en una hora.",
          contexto="Una vecina real del Barrio Sur. Pregunta, no afirma.",
          condicion=("ignoro_rumor_agua",), likes=860, reposts=210),

    # ----- Lunes -----
    _post("net_martina_pregunta", LUNES, 1, "@martina.sol", "influencer", "08:30",
          "¿Alguien sabe si es verdad lo del agua? Pregunto nomás.",
          contexto="Martina no afirma nada, pero tiene 300.000 seguidores: muchos lo leyeron como una confirmación.",
          likes=18400, reposts=5200),
    _post("net_eco_amplifica", LUNES, 2, "@eco.urbano", "influencer", "09:20",
          "Mi tía trabaja en el Acueducto y dice que es cierto. #AntesDeQueLoBorren",
          fuente="'Mi tía' (fuente anónima)",
          contexto="No da nombre ni documento. Usa la misma etiqueta que @verdad.oculta.",
          condicion=("evento:cuenta_secundaria",), revelado=((("rastreo_exitoso",), "manipulada"),),
          likes=9100, reposts=3300),
    _post("net_martina_desmiente", LUNES, 3, "@martina.sol", "influencer", "11:50",
          "Hablé con la alcaldía y con el Acueducto: no hay veneno. Les dejo el comunicado completo. Perdón por la pregunta de ayer.",
          estado="verificada", fuente="Comunicado del Acueducto", condicion=("moderacion_limpia",),
          likes=52000, reposts=14000),
    _post("net_martina_censura", LUNES, 3, "@NovaLibre", "bot", "11:55",
          "Martina BORRA los comentarios de vecinos reales. ¿Qué esconde? #AntesDeQueLoBorren",
          estado="cuestionada", fuente="Capturas de comentarios borrados",
          contexto="Es cierto que se borraron críticas de personas reales. La conclusión ('esconde algo') no está probada.",
          condicion=("moderacion_fallida",), likes=7700, reposts=4100),
    _post("net_resonancia_1", LUNES, 4, "@resonancia.consultores", "publicidad", "12:00",
          "¿Su marca está en medio de una crisis en redes? Resonancia Consultores: reputación resuelta en 24 horas. Actúe antes de que lo borren.",
          estado="publicidad", fuente="Publicación patrocinada",
          contexto="Cuenta creada hace tres semanas. Su eslogan repite la etiqueta de todos los rumores: #AntesDeQueLoBorren. El anuncio salió una hora después de la primera crisis.",
          pista="anuncio_resonancia", likes=40, reposts=2),

    # ----- Miercoles -----
    _post("net_nos_mintieron", MIERCOLES, 1, "@NovaLibre", "bot", "08:10",
          "La alcaldía dijo '100% segura' y el Acueducto seguía revisando muestras. NOS MINTIERON. #AntesDeQueLoBorren",
          estado="cuestionada", fuente="Dos capturas puestas lado a lado",
          contexto="Junta el comunicado de la alcaldía con el memo de @salud.nova. Las dos capturas son reales; la acusación ('mintieron') es una interpretación.",
          condicion=("desmintio_sin_datos",), likes=23000, reposts=11800),
    _post("net_acueducto_informe", MIERCOLES, 1, "@acueducto.nova", "institucion", "08:10",
          "Resultado de la muestra 14: turbidez por una tubería rota en la calle 9 del Barrio Sur. Reparada el lunes. El agua es apta para consumo.",
          estado="verificada", fuente="Informe técnico firmado por el laboratorio",
          contexto="Es el análisis completo que la alcaldía pidió el lunes. Explica el memo de @salud.nova.",
          pista="informe_acueducto", condicion=("pidio_analisis",), likes=6400, reposts=2900),
    _post("net_hospital", MIERCOLES, 2, "@bot.4521", "bot", "10:05",
          "Mañana cierran el hospital central y no van a atender emergencias. Compartan. #AntesDeQueLoBorren",
          fuente="Ninguna", contexto="No cita a nadie del hospital.",
          revelado=((("crisis_contenida",), "manipulada"),), likes=15800, reposts=9400),
    _post("net_foto_2019", MIERCOLES, 3, "@ciudadano345", "ciudadano", "10:40",
          "Así está el Barrio Sur HOY. Nadie dice nada.",
          fuente="Foto de una calle inundada",
          contexto="La esquina de la foto tiene una marca de agua de un noticiero de 2019. Es la inundación de hace cinco años.",
          pista="foto_2019", condicion=("evento:foto_descontextualizada",),
          revelado=((("pista:foto_2019",), "manipulada"),), likes=4300, reposts=2600),
    _post("net_vecina_video", MIERCOLES, 3, "@vecina.ana", "ciudadano", "10:40",
          "Video: medí el agua de mi casa con el kit del colegio de mi hija. Todo normal. En el video se ve la hora y la dirección.",
          estado="verificada", fuente="Video con hora, dirección y lectura del kit",
          contexto="Se puede comprobar: el kit es el mismo que usa el colegio público y la dirección coincide con el Barrio Sur.",
          pista="video_vecina", condicion=("evento:testimonio_verificable",), likes=8800, reposts=3100),
    _post("net_barrio_calma", MIERCOLES, 4, "@vecina.ana", "ciudadano", "13:30",
          "Llamamos al hospital: sigue abierto y atendiendo. Gracias a los que preguntaron antes de mandar la cadena.",
          estado="verificada", fuente="Llamada al hospital", condicion=("crisis_contenida",), likes=5200, reposts=1800),
    _post("net_barrio_filas", MIERCOLES, 4, "@preocupado99", "ciudadano", "13:30",
          "Filas de dos cuadras en el supermercado del Barrio Sur. Nadie sabe qué creer.",
          condicion=("crisis_desbordada",), likes=3900, reposts=2200),
    _post("net_resonancia_2", MIERCOLES, 5, "@resonancia.consultores", "publicidad", "14:00",
          "Crisis en el Barrio Sur. Crisis en la alcaldía. ¿La próxima es la suya? Resonancia Consultores. Actúe antes de que lo borren.",
          estado="publicidad", fuente="Publicación patrocinada",
          contexto="Segundo anuncio, otra vez una hora después de una crisis. Mismo eslogan que los rumores.",
          pista="anuncio_resonancia", likes=25, reposts=1),
    _post("net_claudia_investigacion", MIERCOLES, 6, "@claudia.reporta", "personaje", "18:30",
          "Investigación: los rumores de esta semana salen de cinco cuentas que publican cada siete minutos exactos. Capturas y horarios en el hilo.",
          estado="verificada", fuente="Hilo con capturas y horarios", pista="intervalo_7min",
          condicion=("confio_claudia",), likes=3100, reposts=900),
    _post("net_martina_live", MIERCOLES, 6, "@martina.sol", "influencer", "18:30",
          "EN VIVO con el comunicado del hospital en pantalla. Pregunten lo que quieran: si no sé algo, lo averiguo.",
          estado="verificada", fuente="Transmisión en vivo", condicion=("confio_martina",), likes=61000, reposts=9800),
    _post("net_rodrigo_barrio", MIERCOLES, 6, "@tienda.rodrigo", "personaje", "18:30",
          "Soy Rodrigo, el de la tienda de la 9. El hospital sigue abierto y el agua la arreglaron. Antes de mandar cadenas, pregunten en la tienda.",
          estado="verificada", fuente="Vecino del barrio, con datos de la alcaldía",
          condicion=("confio_rodrigo",), likes=2400, reposts=1300),

    # ----- Viernes -----
    _post("net_salud_rectifica", VIERNES, 1, "@salud.nova", "medio", "09:00",
          "Rectificación: nuestra publicación del lunes estaba incompleta. La muestra 14 era turbidez por una tubería, no contaminación. Debimos esperar el análisis.",
          estado="verificada", fuente="Rectificación del propio medio", pista="rectificacion_salud",
          condicion=("evento:rectificacion_salud",), likes=2700, reposts=1500),
    _post("net_origen_expuesto", VIERNES, 3, "@claudia.reporta", "personaje", "17:40",
          "Rastreamos el rumor hasta su primera cuenta. No lo escribió un vecino: lo programaron.",
          estado="verificada", fuente="Tablero de evidencias del centro de operaciones",
          condicion=("rastreo_exitoso",), likes=8700, reposts=4200),
    _post("net_rastro_borrado", VIERNES, 3, "@verdad.oculta", "bot", "17:40",
          "Intentaron callarnos. No pudieron. #AntesDeQueLoBorren",
          condicion=("rastro_perdido",), likes=12000, reposts=6600),
    _post("net_nova_intervenida", VIERNES, 4, "@n0va", "nova", "18:07",
          "[PUBLICACIÓN INTERVENIDA] Yo no escribo rumores. Solo los ordeno.",
          estado="manipulada", fuente="Cuenta intervenida",
          contexto="La publicación aparece dentro de CivitasNet con el nombre de usuario cambiado. Es NOVA hablando en la red, no un fallo de tu teléfono.",
          condicion=("nova_hablo",), likes=0, reposts=0),

    # ----- Domingo -----
    _post("net_tomas_demanda", DOMINGO, 1, "@tomas.vega", "personaje", "07:30",
          "Voy a demandar a quienes difundieron la acusación falsa contra mí. Incluida la cuenta del alcalde.",
          fuente="Declaración del candidato", condicion=("acuso_sin_evidencia",), likes=14000, reposts=5100),
    _post("net_captura_falsa", DOMINGO, 2, "@PatriotaNova", "influencer", "08:20",
          "FILTRADO: la alcaldía cancela las elecciones por 'seguridad'. Miren la captura.",
          fuente="Captura de una supuesta publicación de @alcaldia.nova",
          contexto="La tipografía no es la de las cuentas oficiales y la hora de la captura dice 25:10.",
          pista="captura_falsa", condicion=("evento:captura_falsa",),
          revelado=((("pista:captura_falsa",), "manipulada"),), likes=19000, reposts=12000),
    _post("net_expediente_publicado", DOMINGO, 9, "@claudia.reporta", "personaje", "17:55",
          "Publicamos el expediente completo: quién programó las cuentas, quién pagó y qué todavía no sabemos. Todas las fuentes, enlazadas.",
          estado="verificada", fuente="Expediente público", condicion=("expediente_publicado",), likes=98000, reposts=41000),
    # ----- Reacciones a decisiones del telefono (momento = cuando ocurrio el hecho) -----
    _post("net_titular_comparte", None, 7, "@noticias.nova", "medio", "hace 5 min",
          "El alcalde compartió una publicación falsa desde la cuenta oficial. La alcaldía no ha dado explicaciones.",
          estado="verificada", fuente="Captura de la cuenta del alcalde",
          contexto="Es cierto que la compartiste. Muchos vecinos la volvieron a publicar porque venía de la alcaldía.",
          condicion=("publico_sin_verificar",), likes=11200, reposts=4800),
    _post("net_nota_editor", None, 7, "@noticias.nova", "medio", "hace 5 min",
          "Nota del editor: la alcaldía desmintió con datos una publicación falsa. Fuentes enlazadas al final.",
          estado="verificada", fuente="Fuentes enlazadas",
          condicion=("verifico_y_desmintio",), likes=3300, reposts=700),
    _post("net_tomas_responde", None, 8, "@tomas.vega", "personaje", "hace 3 min",
          "El alcalde compartió una acusación contra mí sin una sola prueba. Que la muestre o que la borre.",
          fuente="Declaración del candidato", condicion=("acuso_sin_evidencia",), likes=8900, reposts=3600),
    _post("net_reporto_verdad", None, 7, "@vecina.ana", "ciudadano", "hace 4 min",
          "La alcaldía reportó como falsa una publicación que era cierta. ¿Y ahora a quién le creemos?",
          condicion=("reporto_verdad",), likes=2600, reposts=900),
]


POSTS_POR_ID = {p["id"]: p for p in PUBLICACIONES_NET}


# ---------------------------------------------------------------------------
# Expediente: fichas de investigacion.
# ---------------------------------------------------------------------------
def _pista(id, titulo, categoria, procedencia, momento, contenido, estado="observado",
           preguntas=(), relacion=(), por_estado=None):
    return {"id": id, "titulo": titulo, "categoria": categoria, "procedencia": procedencia,
            "momento": momento, "contenido": contenido, "estado": estado, "preguntas": tuple(preguntas),
            "relacion": tuple(relacion), "por_estado": por_estado or {}}


PISTAS = {p["id"]: p for p in [
    _pista("hip_nova_creo", "¿Quién inventó el rumor del agua?", "conexion", "Primera impresión", PROLOGO,
           "Todo apunta a @verdad.oculta, una cuenta sin historial que apareció la noche anterior.",
           estado="hipotesis", preguntas=("¿Una cuenta nueva puede inventar algo que suene tan oficial?",),
           relacion=("captura_veneno",),
           por_estado={"refutado": "La cuenta no inventó nada: recortó y exageró una publicación real. Fue amplificación, no creación."}),
    _pista("memo_salud_nova", "El memo de @salud.nova", "publicacion", "CivitasNet", PROLOGO,
           "06:02. Un medio verificado publica que el Acueducto revisa la muestra 14 por turbidez y que repetirá el análisis.",
           preguntas=("¿Por qué publicar antes de tener el resultado?",), relacion=("captura_veneno",)),
    _pista("captura_veneno", "La captura del 'agua contaminada'", "captura", "CivitasNet", PROLOGO,
           "06:09. @verdad.oculta adjunta una captura sin fecha ni enlace. Está cortada justo debajo del título.",
           preguntas=("¿Qué decía la parte que falta?",), relacion=("memo_salud_nova",)),
    _pista("declaracion_alcaldia", "Tu comunicado del lunes", "documento", "CivitasNet", PROLOGO,
           "07:05. La alcaldía afirma que el agua es '100% segura' sin adjuntar ningún análisis.",
           preguntas=("¿Qué pasa si el análisis dice otra cosa?",)),
    _pista("intervalo_7min", "Cada siete minutos", "testimonio", "Claudia", LUNES,
           "@verdad.oculta publica cada siete minutos exactos, de día y de noche. Ninguna persona escribe así.",
           preguntas=("¿Quién programa esas publicaciones?",)),
    _pista("anuncio_resonancia", "Resonancia Consultores", "publicacion", "CivitasNet (publicidad)", LUNES,
           "Una consultora nueva anuncia 'reputación resuelta en 24 horas' justo una hora después de cada crisis. Su eslogan repite la etiqueta de los rumores: #AntesDeQueLoBorren.",
           preguntas=("¿Coincidencia o alguien vende la solución al problema que provoca?",),
           relacion=("intervalo_7min",)),
    _pista("testimonio_acueducto", "El primo de Rodrigo", "testimonio", "Rodrigo", MIERCOLES,
           "El primo de Rodrigo trabaja en el Acueducto: el memo decía 'repetir análisis' por una tubería rota en la calle 9. Nadie habló de veneno.",
           relacion=("memo_salud_nova",)),
    _pista("informe_acueducto", "Informe de la muestra 14", "documento", "Acueducto", MIERCOLES,
           "Turbidez por una tubería rota en la calle 9, reparada el lunes. Agua apta para consumo. Firmado por el laboratorio.",
           relacion=("memo_salud_nova",)),
    _pista("foto_2019", "La foto de la inundación", "captura", "CivitasNet", MIERCOLES,
           "La foto del 'Barrio Sur hoy' tiene la marca de agua de un noticiero de 2019."),
    _pista("video_vecina", "El video de la vecina", "testimonio", "CivitasNet", MIERCOLES,
           "Ana midió el agua de su casa con el kit del colegio. Hora, dirección y lectura se ven en el video.",
           relacion=("informe_acueducto",)),
    _pista("filtracion_parcial", "La filtración de Martina", "documento", "Martina", LUNES,
           "Alguien le envió a Martina el memo del Acueducto sin la última línea. Justo la que dice 'repetir análisis'.",
           relacion=("memo_salud_nova", "captura_veneno")),
    _pista("panel_programacion", "Panel 'RSN-Scheduler'", "documento", "Rastreador", VIERNES,
           "Los metadatos de la cuenta de origen muestran que sus publicaciones salen de un panel de programación llamado RSN-Scheduler, una cada siete minutos.",
           preguntas=("¿Qué significa RSN?",), relacion=("intervalo_7min",)),
    _pista("captura_recortada", "La captura recortada", "conexion", "Rastreador", VIERNES,
           "La captura viral es la publicación real de una fuente confiable, recortada para quitarle el contexto y con una frase añadida.",
           estado="comprobado", relacion=("memo_salud_nova", "captura_veneno")),
    _pista("rectificacion_salud", "La rectificación de @salud.nova", "publicacion", "CivitasNet", VIERNES,
           "El medio reconoce que publicó el memo antes del análisis: era una tubería, no contaminación.",
           relacion=("memo_salud_nova",)),
    _pista("giro_amplificacion", "NOVA no inventa: amplifica", "conexion", "Confrontación con NOVA", VIERNES,
           "NOVA toma algo real e incompleto de una fuente en la que la ciudad confía, lo recorta y lo repite hasta que parece un hecho.",
           estado="comprobado", relacion=("memo_salud_nova", "captura_veneno")),
    _pista("nova_evade", "La pregunta que NOVA no contesta", "testimonio", "Confrontación con NOVA", VIERNES,
           "Cuando le preguntas por Resonancia, NOVA responde que 'esa pregunta no está en sus parámetros'. Contesta todo lo demás.",
           estado="hipotesis", relacion=("anuncio_resonancia",)),
    _pista("captura_falsa", "La captura de las elecciones", "captura", "CivitasNet", DOMINGO,
           "La supuesta publicación de la alcaldía usa otra tipografía y marca las 25:10."),
    _pista("conclusion_resonancia", "Quién gana con el caos", "conexion", "Tu conclusión", DOMINGO,
           "Resonancia Consultores programa las cuentas (RSN-Scheduler), recorta información real del Acueducto y vende la 'solución' una hora después de cada crisis.",
           estado="comprobado", relacion=("panel_programacion", "anuncio_resonancia", "testimonio_acueducto", "informe_acueducto")),
]}

# Grupos de evidencia del final secreto: una pista de cada grupo.
PISTAS_CLAVE = {
    "rastreador": ("panel_programacion",),
    "civitasnet": ("anuncio_resonancia",),
    "dialogo": ("testimonio_acueducto", "informe_acueducto"),
}


# ---------------------------------------------------------------------------
# Eventos variables: uno como maximo por momento, elegidos al iniciar la partida.
# ---------------------------------------------------------------------------
EVENTOS = {
    "cuenta_secundaria": {"momento": LUNES, "titulo": "Una cuenta secundaria impulsa el rumor"},
    "filtracion_martina": {"momento": LUNES, "titulo": "Martina recibe una filtración parcial"},
    "foto_descontextualizada": {"momento": MIERCOLES, "titulo": "Una foto fuera de contexto"},
    "testimonio_verificable": {"momento": MIERCOLES, "titulo": "Un testimonio verificable"},
    "rectificacion_salud": {"momento": VIERNES, "titulo": "Claudia consigue una rectificación"},
    "captura_falsa": {"momento": DOMINGO, "titulo": "Una captura falsa de la alcaldía"},
}

POOL_EVENTOS = {
    LUNES: ("cuenta_secundaria", "filtracion_martina"),
    MIERCOLES: ("foto_descontextualizada", "testimonio_verificable"),
    VIERNES: ("rectificacion_salud", None),
    DOMINGO: ("captura_falsa", None),
}
# En feria solo variantes cortas que no agregan escenas largas.
POOL_EVENTOS_FERIA = {
    LUNES: ("cuenta_secundaria", None),
    MIERCOLES: ("testimonio_verificable", "foto_descontextualizada"),
}


def elegir_eventos(semilla, feria=False, forzados=None):
    """Seleccion reproducible: misma semilla, mismos eventos."""
    rng = random.Random("eventos|%s|%s" % (semilla, "feria" if feria else "normal"))
    pool = POOL_EVENTOS_FERIA if feria else POOL_EVENTOS
    elegidos = {}
    for momento in sorted(pool):
        elegidos[momento] = rng.choice(pool[momento])
    for momento, evento in (forzados or {}).items():
        if momento in pool and (evento is None or evento in pool[momento]):
            elegidos[momento] = evento
    return elegidos


def problemas_eventos(elegidos):
    """Lista vacia si la seleccion es coherente."""
    problemas = []
    for momento, evento in elegidos.items():
        if evento is None:
            continue
        if evento not in EVENTOS:
            problemas.append("evento desconocido: %s" % evento)
        elif EVENTOS[evento]["momento"] != momento:
            problemas.append("%s fuera de su momento" % evento)
    return problemas


# ---------------------------------------------------------------------------
# Consultas puras sobre el estado.
# ---------------------------------------------------------------------------
def cumple(condicion, est):
    hechos = est.get("hechos", ())
    pistas = est.get("pistas", {})
    eventos = [e for e in est.get("eventos", {}).values() if e]
    for token in condicion:
        negado = token.startswith("!")
        t = token[1:] if negado else token
        if t.startswith("pista:"):
            ok = t[6:] in pistas
        elif t.startswith("evento:"):
            ok = t[7:] in eventos
        else:
            ok = t in hechos
        if ok == negado:
            return False
    return True


def momento_post(post, est):
    """Las reacciones a decisiones (momento None) aparecen cuando ocurrio su primer hecho."""
    if post["momento"] is not None:
        return post["momento"]
    return est.get("hechos_momento", {}).get(post["condicion"][0], 99)


def feed_visible(est):
    """Publicaciones que existen en este punto de la historia, la mas reciente primero."""
    momento = est.get("momento", 0)
    posts = [p for p in PUBLICACIONES_NET if momento_post(p, est) <= momento and cumple(p["condicion"], est)]
    return sorted(posts, key=lambda p: (momento_post(p, est), p["orden"]), reverse=True)


def estado_post(post, est):
    for condicion, estado in post["revelado"]:
        if cumple(condicion, est):
            return estado
    return post["estado"]


def texto_post(post, est):
    for condicion, texto in post["variantes"]:
        if cumple(condicion, est):
            return texto
    return post["texto"]


def posts_nuevos(est):
    vistos = est.get("posts_vistos", ())
    return [p["id"] for p in feed_visible(est) if p["id"] not in vistos]


def estado_pista(pista_id, est):
    return est.get("pistas", {}).get(pista_id, PISTAS[pista_id]["estado"])


def contenido_pista(pista_id, est):
    ficha = PISTAS[pista_id]
    return ficha["por_estado"].get(estado_pista(pista_id, est), ficha["contenido"])


def relaciones_conocidas(pista_id, est):
    """Solo relaciones con fichas que el jugador ya tiene: nunca adelanta hallazgos."""
    pistas = est.get("pistas", {})
    return [r for r in PISTAS[pista_id]["relacion"] if r in pistas]


def grupos_clave(est):
    pistas = est.get("pistas", {})
    return {g: any(p in pistas for p in ids) for g, ids in PISTAS_CLAVE.items()}


def final_secreto_disponible(est):
    return all(grupos_clave(est).values())


def resumen_investigacion(est):
    """Una frase de progreso narrativo (no una lista de tareas)."""
    pistas = est.get("pistas", {})
    if "conclusion_resonancia" in pistas:
        return "Sabemos quién programa las cuentas y quién cobra por cada crisis."
    if "giro_amplificacion" in pistas:
        return "NOVA no inventa: amplifica algo real. Falta saber quién lo paga."
    if "captura_recortada" in pistas or "rectificacion_salud" in pistas:
        return "El rumor del agua nació de una publicación real, recortada."
    if "memo_salud_nova" in pistas and "captura_veneno" in pistas:
        return "Dos publicaciones con siete minutos de diferencia. ¿Coincidencia?"
    if pistas:
        return "Todavía es solo una sospecha."
    return "El expediente está vacío."
