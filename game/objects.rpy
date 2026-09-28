init python:
    from clases.Publicacion import SesionPublicacion, BancoPublicaciones, armar_publicacion
    from clases.Ciudad import Ciudad
    from clases.Jugador import Jugador

    def aplicar_consecuencia(consecuencia):
        if not consecuencia:
            return
        for clave, valor in consecuencia.items():
            if clave == 'puntos':
                if valor > 0:
                    store.jugador.ganar_puntos(valor)
                else:
                    store.jugador.perder_puntos(-valor)
            elif clave == 'reputacion':
                store.jugador.reputacion = max(0, min(100, store.jugador.reputacion + valor))
            elif hasattr(store.ciudad, clave):
                nuevo = max(0, min(100, getattr(store.ciudad, clave) + valor))
                setattr(store.ciudad, clave, nuevo)

label nueva_publicacion:
    if not banco.hay_mas():
        return

    $ sesion = SesionPublicacion(banco.siguiente())

    "Recibiste una publicacion nueva en Civitas."
    "[sesion.publicacion.autor]: [sesion.publicacion.contenido]"
    "[sesion.actual.texto]"

    while not sesion.terminada():
        $ eleccion = renpy.display_menu(sesion.opciones())
        $ sesion.elegir(eleccion)
        "[sesion.actual.texto]"

    $ aplicar_consecuencia(sesion.actual.consecuencia)

    $ razon_derrota = ciudad.derrota_inmediata() or ""
    if razon_derrota:
        jump derrota

    return

# Personajes

define inf = Character("Influencer")
define may = Character("Candidato a Alcalde")
define inv = Character("Investigador")
define ci = Character("Civil")

# Estado de la ciudad y del jugador

default ciudad = Ciudad()
default jugador = Jugador("Alcalde")
default razon_derrota = ""

# Banco de publicaciones — insertadas en AVL por nivel_riesgo, entregadas de menor a mayor

default banco = BancoPublicaciones([

    armar_publicacion(
        "@verde.ciudad", "El colegio San Marcos lanzo una campana de reciclaje para reducir residuos.",
        False, 10,
        "?Como apoyas la iniciativa?",
        {"etiqueta": "Compartir y promover activamente",
         "texto": "La comunidad se suma. El bienestar de Ciudad Nova mejora.",
         "efecto": {"bienestar": 3, "confianza": 2, "puntos": 5}},
        {"etiqueta": "No hacer nada",
         "texto": "La oportunidad pasa desapercibida.",
         "efecto": {"bienestar": -1}},
    ),

    armar_publicacion(
        "@salud.nova", "La alcaldia inauguro el nuevo hospital del sur esta manana.",
        False, 15,
        "?Como reaccionas ante esta noticia verificada?",
        {"etiqueta": "Difundir activamente con datos",
         "texto": "Los ciudadanos confian en la informacion oficial. Excelente gestion.",
         "efecto": {"bienestar": 5, "confianza": 3, "info_verificada": 3, "puntos": 8}},
        {"etiqueta": "Dejar que circule sola",
         "texto": "La noticia llega lento. Oportunidad perdida.",
         "efecto": {"bienestar": -1}},
    ),

    armar_publicacion(
        "@candidata.luna", "Propongo convertir el lote abandonado del barrio norte en zona verde para las familias.",
        False, 20,
        "?Como respondes a esta propuesta?",
        {"etiqueta": "Apoyar con evidencia de impacto",
         "texto": "La propuesta gana respaldo ciudadano. La ciudad florece.",
         "efecto": {"bienestar": 2, "confianza": 2, "puntos": 5}},
        {"etiqueta": "Ignorar la propuesta",
         "texto": "Los ciudadanos sienten que nadie escucha.",
         "efecto": {"convivencia": -1}},
    ),

    armar_publicacion(
        "@barrio.central", "Vecinos del barrio central llevan tres semanas sin alumbrado publico.",
        False, 30,
        "?Que haces con esta solicitud ciudadana?",
        {"etiqueta": "Gestionar y comunicar acciones",
         "texto": "La gente siente que su voz importa. La convivencia mejora.",
         "efecto": {"convivencia": 3, "confianza": 2, "bienestar": 2, "puntos": 6}},
        {"etiqueta": "Ignorar el pedido",
         "texto": "Los vecinos pierden la fe en las instituciones.",
         "efecto": {"convivencia": -2, "confianza": -2}},
    ),

    armar_publicacion(
        "@salud.publica", "Se registraron 40 casos de gripe en escuelas del centro. Las autoridades investigan.",
        False, 40,
        "?Como manejas esta informacion de salud publica?",
        {"etiqueta": "Informar con datos medicos verificados",
         "texto": "La ciudadania actua con calma y prevencion. Buen manejo de crisis.",
         "efecto": {"info_verificada": 4, "confianza": 2, "puntos": 8}},
        {"etiqueta": "Exagerar la amenaza para generar alarma",
         "texto": "El panico se extiende. Los hospitales se saturan innecesariamente.",
         "efecto": {"desinformacion": 5, "conflictos": 3, "bienestar": -4}},
    ),

    armar_publicacion(
        "@preocupado99", "Dicen que el gobierno va a privatizar el acueducto. Ya no tendremos agua gratis.",
        True, 55,
        "?Que haces con este rumor sobre el acueducto?",
        {"etiqueta": "Desmentir con evidencia oficial",
         "texto": "La verdad prevalece. La confianza en las instituciones se fortalece.",
         "efecto": {"reputacion": 8, "confianza": 3, "desinformacion": -4, "puntos": 10}},
        {"etiqueta": "No tomar accion",
         "texto": "El rumor se expande. Los ciudadanos entran en conflicto.",
         "efecto": {"conflictos": 4, "desinformacion": 3, "confianza": -3}},
    ),

    armar_publicacion(
        "@noticias.nova", "Fuentes anonimas afirman que el alcalde ordenara el cierre de todos los parques.",
        True, 60,
        "?Como actuas frente a este rumor sobre los parques?",
        {"etiqueta": "Verificar con fuentes oficiales antes de actuar",
         "texto": "Confirmas que es falso y lo comunicas. La ciudad respira tranquila.",
         "efecto": {"info_verificada": 5, "confianza": 2, "puntos": 8}},
        {"etiqueta": "Compartir la noticia sin verificar",
         "texto": "El rumor llega a miles. Los conflictos aumentan por la incertidumbre.",
         "efecto": {"conflictos": 5, "desinformacion": 4, "convivencia": -3}},
    ),

    armar_publicacion(
        "@sol.y.limon", "Escuche que el alcalde robo fondos publicos para comprar su casa. Lo vi en un video.",
        True, 75,
        "?Como respondes a esta acusacion grave?",
        {"etiqueta": "Desmentir con datos y transparencia",
         "texto": "La gente te cree. Tu reputacion se consolida.",
         "efecto": {"reputacion": 10, "confianza": 5, "desinformacion": -4, "puntos": 12}},
        {"etiqueta": "Ignorar la acusacion",
         "texto": "El rumor crece y la gente duda de ti.",
         "efecto": {"reputacion": -8, "desinformacion": 5}},
    ),

    armar_publicacion(
        "@investigador.nova", "Tengo pruebas de que el candidato Tomas tiene vinculos con grupos criminales.",
        True, 85,
        "?Que haces con esta grave acusacion sin verificar?",
        {"etiqueta": "Reportar a autoridades y documentar",
         "texto": "Actuas con responsabilidad. Los conflictos disminuyen.",
         "efecto": {"reputacion": 8, "conflictos": -3, "desinformacion": -3, "puntos": 10}},
        {"etiqueta": "Difundir sin verificar para 'informar'",
         "texto": "La ciudad entra en caos. Una acusacion falsa destruye reputaciones.",
         "efecto": {"desinformacion": 6, "conflictos": 5, "confianza": -5}},
    ),

    armar_publicacion(
        "@ciudadano", "El candidato a alcalde ha sido acusado de corrupcion por 3 millones de pesos.",
        True, 90,
        "?Como manejas esta grave acusacion en plena campana electoral?",
        {"etiqueta": "Investigar a fondo y publicar evidencia",
         "texto": "La gente te respalda. La verdad fortalece la democracia.",
         "efecto": {"reputacion": 15, "confianza": 5, "desinformacion": -6, "puntos": 15}},
        {"etiqueta": "Difundir sin verificar para adelantarte",
         "texto": "El rumor se propaga. Si era falso, destruiste a un inocente.",
         "efecto": {"reputacion": -15, "desinformacion": 8, "conflictos": 6}},
    ),

])
