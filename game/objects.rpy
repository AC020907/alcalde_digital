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
# Cada publicacion tiene 4 acciones segun el diagrama del PDF (pag. 4):
#   Compartir | Verificar (Si/No) | Ignorar

default banco = BancoPublicaciones([

    armar_publicacion(
        "@verde.ciudad",
        "El colegio San Marcos lanzo una campana de reciclaje.",
        False, 10,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La difundes de inmediato. La comunidad se suma y el bienestar mejora.",
            "efecto": {"bienestar": 3, "confianza": 1, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La oportunidad pasa desapercibida. Nada cambia.",
            "efecto": {"bienestar": -1}},
        verificar_si={
            "etiqueta": "Si, es verdadera — Compartir",
            "texto": "Verificas y confirmas. La difundes con credibilidad. Excelente gestion.",
            "efecto": {"bienestar": 5, "confianza": 3, "info_verificada": 3, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es falsa — Reportar",
            "texto": "Detectas que es falsa y la reportas. Ciudad Nova te lo agradece.",
            "efecto": {"desinformacion": -3, "confianza": 2, "puntos": 6}},
    ),

    armar_publicacion(
        "@salud.nova",
        "La alcaldia inauguro el nuevo hospital del sur esta manana.",
        False, 15,
        compartir={
            "etiqueta": "Compartir",
            "texto": "Los ciudadanos reciben la buena noticia. La confianza en instituciones crece.",
            "efecto": {"bienestar": 4, "confianza": 2, "puntos": 5}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La noticia no llega a tiempo. Oportunidad perdida.",
            "efecto": {"bienestar": -1}},
        verificar_si={
            "etiqueta": "Si, es verdadera — Compartir",
            "texto": "Confirmas con la alcaldia y difundes con datos. Gestion ejemplar.",
            "efecto": {"bienestar": 6, "confianza": 4, "info_verificada": 3, "puntos": 10}},
        verificar_no={
            "etiqueta": "No, es falsa — Reportar",
            "texto": "Era un rumor. Lo reportas y evitas confusion ciudadana.",
            "efecto": {"desinformacion": -3, "confianza": 3, "puntos": 7}},
    ),

    armar_publicacion(
        "@candidata.luna",
        "Propongo convertir el lote abandonado del barrio norte en zona verde.",
        False, 20,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La propuesta gana respaldo ciudadano. La ciudad florece.",
            "efecto": {"bienestar": 2, "confianza": 2, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "Los ciudadanos sienten que nadie escucha las propuestas.",
            "efecto": {"convivencia": -1}},
        verificar_si={
            "etiqueta": "Si, es seria — Compartir con contexto",
            "texto": "Verificas la propuesta y la apoyas con datos. Gran impacto.",
            "efecto": {"bienestar": 4, "confianza": 3, "convivencia": 2, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es propaganda — Reportar",
            "texto": "Detectas que es solo propaganda electoral. La reportas.",
            "efecto": {"desinformacion": -2, "confianza": 1, "puntos": 5}},
    ),

    armar_publicacion(
        "@barrio.central",
        "Vecinos del barrio central llevan tres semanas sin alumbrado publico.",
        False, 30,
        compartir={
            "etiqueta": "Compartir",
            "texto": "Visibilizas el problema. La gente siente que su voz importa.",
            "efecto": {"convivencia": 2, "confianza": 1, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "Los vecinos pierden la fe en las instituciones.",
            "efecto": {"convivencia": -2, "confianza": -2}},
        verificar_si={
            "etiqueta": "Si, es real — Gestionar y comunicar acciones",
            "texto": "Verificas y canalizas la queja oficial. La convivencia mejora.",
            "efecto": {"convivencia": 4, "confianza": 3, "bienestar": 2, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es exagerado — Reportar",
            "texto": "Era una exageracion. La reportas para no generar alarma falsa.",
            "efecto": {"desinformacion": -2, "convivencia": 1, "puntos": 4}},
    ),

    armar_publicacion(
        "@salud.publica",
        "Se registraron 40 casos de gripe en escuelas del centro. Las autoridades investigan.",
        False, 40,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La ciudadania actua con prevencion. Buen manejo de la informacion.",
            "efecto": {"info_verificada": 2, "bienestar": 1, "puntos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "Los ciudadanos no saben de la alerta. Se siguen contagiando.",
            "efecto": {"bienestar": -3, "desinformacion": 2}},
        verificar_si={
            "etiqueta": "Si, es verdadera — Informar con datos medicos",
            "texto": "Confirmas con autoridades de salud y difundes con calma. Excelente.",
            "efecto": {"info_verificada": 5, "confianza": 3, "bienestar": 3, "puntos": 10}},
        verificar_no={
            "etiqueta": "No, es exagerado — Reportar para evitar panico",
            "texto": "Evitas el panico colectivo. Ciudad Nova respira tranquila.",
            "efecto": {"desinformacion": -4, "conflictos": -2, "puntos": 7}},
    ),

    armar_publicacion(
        "@preocupado99",
        "Dicen que el gobierno va a privatizar el acueducto. Ya no tendremos agua gratis.",
        True, 55,
        compartir={
            "etiqueta": "Compartir",
            "texto": "El rumor se propaga rapidamente. Los ciudadanos entran en conflicto.",
            "efecto": {"conflictos": 5, "desinformacion": 4, "confianza": -3}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "El rumor sigue circulando sin respuesta. La tension aumenta.",
            "efecto": {"conflictos": 2, "desinformacion": 2}},
        verificar_si={
            "etiqueta": "Si, es verdad — Compartir con evidencia oficial",
            "texto": "Verificas y resulta verdadero. Lo informas con fuentes. Ciudad confía.",
            "efecto": {"info_verificada": 4, "confianza": 3, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es falso — Reportar y desmentir",
            "texto": "La verdad prevalece. La confianza en las instituciones se fortalece.",
            "efecto": {"reputacion": 6, "confianza": 4, "desinformacion": -5, "puntos": 12}},
    ),

    armar_publicacion(
        "@noticias.nova",
        "Fuentes anonimas afirman que el alcalde ordenara el cierre de todos los parques.",
        True, 60,
        compartir={
            "etiqueta": "Compartir",
            "texto": "El rumor llega a miles. Los conflictos aumentan por la incertidumbre.",
            "efecto": {"conflictos": 5, "desinformacion": 4, "convivencia": -3}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "El rumor circula sin freno. La tension sigue creciendo.",
            "efecto": {"conflictos": 2, "desinformacion": 3}},
        verificar_si={
            "etiqueta": "Si, es verdad — Informar con datos oficiales",
            "texto": "Confirmas la noticia con el alcalde y la comunicas claramente.",
            "efecto": {"info_verificada": 4, "confianza": 2, "puntos": 7}},
        verificar_no={
            "etiqueta": "No, es falso — Reportar y comunicar la verdad",
            "texto": "Confirmas que es falso y lo comunicas. La ciudad respira tranquila.",
            "efecto": {"info_verificada": 5, "confianza": 3, "desinformacion": -4, "puntos": 10}},
    ),

    armar_publicacion(
        "@sol.y.limon",
        "Escuche que el alcalde robo fondos publicos para comprar su casa. Lo vi en un video.",
        True, 75,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La acusacion se viraliza. Si era falsa, destruiste a un inocente.",
            "efecto": {"reputacion": -8, "desinformacion": 5, "conflictos": 4}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "El rumor crece y la gente duda de las instituciones.",
            "efecto": {"reputacion": -4, "desinformacion": 3}},
        verificar_si={
            "etiqueta": "Si, hay evidencia — Compartir con pruebas",
            "texto": "Verificas y hay evidencia real. Lo comunicas con responsabilidad.",
            "efecto": {"info_verificada": 5, "confianza": 2, "puntos": 8}},
        verificar_no={
            "etiqueta": "No, es falso — Reportar y desmentir",
            "texto": "La gente te cree. Tu reputacion se consolida. La verdad gana.",
            "efecto": {"reputacion": 10, "confianza": 5, "desinformacion": -5, "puntos": 14}},
    ),

    armar_publicacion(
        "@investigador.nova",
        "Tengo pruebas de que el candidato Tomas tiene vinculos con grupos criminales.",
        True, 85,
        compartir={
            "etiqueta": "Compartir",
            "texto": "La ciudad entra en caos. Una acusacion sin verificar destruye reputaciones.",
            "efecto": {"desinformacion": 6, "conflictos": 5, "confianza": -5}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La grave acusacion queda sin respuesta. La incertidumbre crece.",
            "efecto": {"conflictos": 3, "desinformacion": 2}},
        verificar_si={
            "etiqueta": "Si, hay evidencia — Reportar a autoridades",
            "texto": "Actuas con responsabilidad. Las autoridades investigan. Los conflictos bajan.",
            "efecto": {"reputacion": 8, "conflictos": -4, "desinformacion": -3, "puntos": 12}},
        verificar_no={
            "etiqueta": "No, es fabricado — Reportar la manipulacion",
            "texto": "Expones la manipulacion. Ciudad Nova se protege de la desinformacion.",
            "efecto": {"info_verificada": 5, "confianza": 3, "desinformacion": -4, "puntos": 10}},
    ),

    armar_publicacion(
        "@ciudadano",
        "El candidato a alcalde ha sido acusado de corrupcion por 3 millones de pesos.",
        True, 90,
        compartir={
            "etiqueta": "Compartir",
            "texto": "El rumor se propaga. Si era falso, destruiste a un inocente y pierdes credibilidad.",
            "efecto": {"reputacion": -15, "desinformacion": 8, "conflictos": 6}},
        ignorar={
            "etiqueta": "Ignorar",
            "texto": "La acusacion sigue circulando sin respuesta. La desconfianza aumenta.",
            "efecto": {"conflictos": 4, "confianza": -3, "desinformacion": 3}},
        verificar_si={
            "etiqueta": "Si, hay evidencia — Investigar y publicar pruebas",
            "texto": "La gente te respalda. La verdad fortalece la democracia.",
            "efecto": {"reputacion": 15, "confianza": 5, "desinformacion": -6, "puntos": 15}},
        verificar_no={
            "etiqueta": "No, es falsa — Reportar y exigir rectificacion",
            "texto": "Proteges al acusado inocente. La transparencia gana. Ciudad Nova prospera.",
            "efecto": {"reputacion": 12, "info_verificada": 6, "confianza": 4, "puntos": 12}},
    ),

])
