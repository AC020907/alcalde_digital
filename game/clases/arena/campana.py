"""
Campana de la Arena Online: UNA historia compartida vista desde cuatro perspectivas.

Cada ronda tiene: escena comun (la ven todos) -> pista privada (solo la ve el rol) -> reto competitivo (lo juegan
TODOS) -> decision civica ligada a lo vivido -> consecuencia sobre la misma ciudad.
Las pistas privadas son complementarias: ninguna resuelve el reto, pero juntas explican la crisis. Si un rol no
esta en la sala, su aportacion la da un personaje (linea "ausente"), asi el argumento nunca se bloquea.

Personajes de la Historia que acompanan a cada rol: Rodrigo (Ciudadano), Claudia (Periodista), Martina
(Influencer) y Tomas (Candidato). NOVA es la red de cuentas automaticas.
"""

MENTOR = {"ciudadano": "rodrigo", "periodista": "claudia", "influencer": "martina", "candidato": "tomas"}
NOMBRE = {"rodrigo": "Rodrigo", "claudia": "Claudia Reyes", "martina": "Martina Sol", "tomas": "Tomás Vega",
          "nova": "NOVA", "civitas": "CivitasNet", "narrador": ""}
SEGUNDOS_ESCENA = 40          # tiempo maximo de lectura; se avanza antes si todos pulsan «Listo»

RONDAS = (
    {
        "reto": "moderador", "protagonista": "ciudadano", "evento": "discusion",
        "titulo": "Lunes · El muro del barrio",
        "comun": [("narrador", "Faltan seis días para las elecciones. Una cuenta sin foto asegura que el agua de Ciudad Nova está envenenada."),
                  ("civitas", "Tendencia nº 1: #AguaEnvenenada · 40.000 reposts en una hora."),
                  ("rodrigo", "En el grupo del barrio ya no se puede hablar: entre insultos y cuentas raras, nadie sabe a quién creer.")],
        "privada": {
            "ciudadano": ("rodrigo", "Mi vecina doña Elsa escribió que el alcalde responde tarde. Es una queja, no un bot: tiene su cuenta desde 2016. Que no la borren por decir lo que piensa."),
            "periodista": ("claudia", "Mira las fechas: muchas cuentas que gritan «veneno» se crearon esta misma semana. Una cuenta nueva no prueba nada sola, pero veinte iguales sí."),
            "influencer": ("martina", "Los comentarios que más suben repiten la misma frase, palabra por palabra. Eso no es gente opinando: es copiar y pegar."),
            "candidato": ("tomas", "Me llueven críticas a mi campaña. Las que traen argumentos, las leo; las que solo insultan vienen todas a la misma hora."),
        },
        "ausente": ("rodrigo", "Ojo con borrar a los vecinos de siempre solo porque critican."),
        "reto_intro": "Modera el muro: borra bots y ataques, deja pasar la crítica legítima.",
        "decision_intro": "Tras moderar el muro, aparece esto en Civitas. ¿Qué haces con ello?",
    },
    {
        "reto": "rastreador", "protagonista": "periodista", "evento": "noticia_falsa",
        "titulo": "Martes · La cadena del rumor",
        "comun": [("claudia", "El rumor no nació en el barrio. Alguien lo sembró y otros lo fueron pasando. Si reconstruimos la cadena, llegamos al origen."),
                  ("civitas", "Nueva publicación en tendencia. Fuente: desconocida."),
                  ("nova", "…buscan un origen. Qué tierno.")],
        "privada": {
            "ciudadano": ("rodrigo", "A mí me llegó por mi primo, y a él por un grupo de padres del colegio. Nadie recuerda quién lo puso primero."),
            "periodista": ("claudia", "Las horas no mienten: nadie puede reenviar algo antes de recibirlo. Ordena la cadena por hora y desconfía de la cuenta sin historial."),
            "influencer": ("martina", "El salto grande fue cuando una cuenta con muchos seguidores lo compartió. Antes de eso casi nadie lo había visto."),
            "candidato": ("tomas", "Mi equipo recibió el mismo texto por tres canales distintos en diez minutos. Eso es una campaña, no un vecino asustado."),
        },
        "ausente": ("claudia", "Ordena por hora: nadie reenvía algo antes de recibirlo."),
        "reto_intro": "Reconstruye la cadena del rumor hasta su origen y decide qué tipo de cuenta lo creó.",
        "decision_intro": "Ya sabes de dónde salió el rumor. Ahora circula esto:",
    },
    {
        "reto": "contencion", "protagonista": "candidato", "evento": "rumor_candidato",
        "titulo": "Jueves · La noche del debate",
        "comun": [("narrador", "Debate de candidatos en la plaza, en directo. A los diez minutos empieza a circular un audio falso."),
                  ("tomas", "Si contestamos con otro rumor, perdemos todos. Hay que frenarlo cuenta por cuenta antes de que llegue a toda la ciudad."),
                  ("civitas", "Alerta: un rumor salta de cuenta en cuenta por la red de Ciudad Nova.")],
        "privada": {
            "ciudadano": ("rodrigo", "En el barrio el audio entra por dos o tres personas que lo reenvían todo. Si a ellos no les llega, no llega a nadie más."),
            "periodista": ("claudia", "El audio está montado: la voz se corta donde cambia la frase. Lo puedo demostrar, pero necesito que no se extienda mientras tanto."),
            "influencer": ("martina", "Un rumor frenado al principio vale por diez desmentidos después. Las primeras cuentas son las que importan."),
            "candidato": ("tomas", "El audio habla de mi campaña y es falso. No voy a pedir que lo borren por ser crítica: voy a responder con datos."),
        },
        "ausente": ("tomas", "Es un audio falso sobre un candidato. Frénenlo sin responder con otro rumor."),
        "reto_intro": "Caza-Rumores: toca cada rumor mientras viaja por la red, antes de que contagie a otra cuenta.",
        "decision_intro": "El debate terminó y esto sigue circulando sobre un candidato:",
    },
    {
        "reto": "plataformas", "protagonista": "influencer", "evento": "viral",
        "titulo": "Domingo, 6:00 · La Gran Viralización",
        "comun": [("nova", "Todas mis cuentas despiertan a la vez. A dos horas de abrir las urnas, ya no hay tiempo para desmentir nada."),
                  ("martina", "Hay una forma: NOVA guarda los archivos originales. Si alguien entra a su sistema y los saca, el rumor se cae solo."),
                  ("narrador", "La única salida es infiltrarse en el sistema de NOVA y volver con la evidencia.")],
        "privada": {
            "ciudadano": ("rodrigo", "En el barrio dicen que lo que publica NOVA lo paga alguien de fuera. Si hay una factura, tiene que estar ahí dentro."),
            "periodista": ("claudia", "Necesito el análisis original del Acueducto, sin editar. Con ese documento puedo publicar el desmentido completo."),
            "influencer": ("martina", "Yo estuve cerca de esa gente: me ofrecieron un video patrocinado. Sé cómo nombran sus archivos. Recoge todos los fragmentos que veas."),
            "candidato": ("tomas", "Si aparece la lista de cuentas automáticas, las cuatro campañas firmamos juntas el desmentido. Eso sí lo cree la gente."),
        },
        "ausente": ("martina", "Recojan todos los fragmentos: cada uno es una prueba distinta."),
        "reto_intro": "Ruta de la Verdad: corre, salta y rescata los fragmentos de evidencia antes de que NOVA cierre la sesión.",
        "decision_intro": "Con la evidencia en la mano, esto se está volviendo viral:",
    },
    {
        "reto": "ritmo", "protagonista": None, "evento": "noticia_verdadera",
        "titulo": "Domingo, 7:30 · Duelo de Frecuencias",
        "comun": [("narrador", "La transmisión electoral oficial empieza… y la señal se distorsiona."),
                  ("nova", "Si no puedo esconder la evidencia, voy a tapar la señal. Nadie va a oír nada."),
                  ("claudia", "¡Está secuestrando la transmisión! Hay que recuperar la frecuencia nota a nota. Todos, a la vez.")],
        "privada": {
            "ciudadano": ("rodrigo", "Media ciudad está pegada a la radio esperando. Si la señal vuelve limpia, sale a votar tranquila."),
            "periodista": ("claudia", "Tengo el desmentido listo para leer al aire. Solo necesito diez segundos de señal limpia."),
            "influencer": ("martina", "Voy a retransmitirlo en directo. Cuanto más limpio suene, más lejos llega."),
            "candidato": ("tomas", "Gane quien gane hoy, que sea con la gente oyendo la verdad."),
        },
        "ausente": ("claudia", "Recuperen la señal: es lo último que le queda a NOVA."),
        "reto_intro": "Gran final: responde a NOVA nota a nota. Misma canción y mismas notas para todos.",
        "decision_intro": "La señal volvió. Esta es la última publicación antes de abrir las urnas:",
    },
)


def rondas(total):
    """Las `total` rondas de una partida. Con menos de cinco se conservan las ultimas (el Duelo siempre es el final)."""
    total = max(1, min(len(RONDAS), total))
    return RONDAS[len(RONDAS) - total:]


def escena(ronda, rol, roles_presentes):
    """Lo que ve UN jugador antes del reto: escena comun + SOLO su pista privada (+ aportacion de roles ausentes)."""
    r = ronda
    lineas = [{"quien": q, "nombre": NOMBRE[q], "texto": t} for q, t in r["comun"]]
    quien, texto = r["privada"][rol]
    datos = {"titulo": r["titulo"], "comun": lineas, "privada": {"quien": quien, "nombre": NOMBRE[quien], "texto": texto},
             "protagonista": r["protagonista"], "reto": r["reto"], "reto_intro": r["reto_intro"]}
    if r["protagonista"] and r["protagonista"] not in roles_presentes:
        q, t = r["ausente"]
        datos["ausente"] = {"quien": q, "nombre": NOMBRE[q], "texto": t}
    return datos
