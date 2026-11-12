## Piezas compartidas de las rutas narrativas: calidad de decisiones (Puntuacion Civica),
## musica por estado de animo con respaldo, y ayuda de los aliados el domingo.

default decisiones_calidad = {}
default decisiones_pub = []

init -1 python:
    from clases import Puntuacion as puntuacion
    from clases import Destinos as destinos

    def calidad_decision(decision_id, valor):
        """Una entrada por decision; repetir la misma decision no suma dos veces."""
        store.decisiones_calidad[decision_id] = valor

    def registrar_respuesta_publicacion(pub, accion):
        store.decisiones_pub.append((pub.nivel_riesgo, pub.es_falsa, accion))

    MUSICA = {
        "menu":            ("menu.ogg",),
        "conversacion":    ("conversacion.ogg",),
        "investigacion":   ("investigacion.ogg",),
        "calma":           ("calma.ogg",),
        "tension":         ("tension.ogg",),
        "crisis":          ("crisis.ogg",),
        "nova":            ("nova.ogg",),
        "revelacion":      ("revelacion.ogg",),
        "final_informada": ("final_informada.ogg",),
        "final_dividida":  ("final_dividida.ogg",),
        "final_caos":      ("final_caos.ogg",),
        "final_mandato":   ("final_mandato.ogg",),
        "final_secreto":   ("final_secreto.ogg",),
        "creditos":        ("creditos.ogg",),
    }

    def ruta_musica(nombre):
        for archivo in MUSICA[nombre]:
            ruta = "assets/audio/music/" + archivo
            if renpy.loadable(ruta):
                return ruta
        return None

    def musica(nombre, fadein=1.5, fadeout=1.2):
        ruta = ruta_musica(nombre)
        if ruta:
            renpy.music.play(ruta, channel="music", loop=True, fadein=fadein, fadeout=fadeout, if_changed=True)

    SFX = {
        "pista": ("pista.ogg", "rastreo_paso.wav"),
        "logro": ("logro.ogg", "exito.wav"),
        "error": ("error.ogg", "fallo.wav"),
        "decision": ("decision.ogg", "eleccion.wav"),
        "glitch": ("glitch.ogg", "intercepcion.wav"),
        "pagina": ("pagina.ogg", "ui_click.wav"),
        "transicion": ("transicion.ogg", "ui_click.wav"),
        "alarma": ("alarma_viral.wav",),
        "notificacion": ("notificacion.wav",),
    }

    # Avisos visuales de sonido (inclusividad): el mismo evento se lee aunque no se oiga.
    TEXTO_SONIDO = {"pista": "Pista nueva", "logro": "¡Logro!", "error": "Error", "decision": "Decisión registrada",
                    "glitch": "Interferencia", "alarma": "¡Alarma: algo se está viralizando!",
                    "notificacion": "Notificación de Civitas"}

    def sfx(nombre):
        if persistent.avisos_sonido and nombre in TEXTO_SONIDO:
            renpy.show_screen("aviso_sonido", texto=TEXTO_SONIDO[nombre], _tag="aviso_sonido")
        for archivo in SFX[nombre]:
            ruta = "assets/audio/sfx/" + archivo
            if renpy.loadable(ruta):
                renpy.sound.play(ruta)
                return

    def aliado_domingo():
        """Quien ayuda en la Gran Viralizacion: nace de lo que el jugador cultivo durante la semana."""
        if hay("alianza_tomas"):
            return "tomas"
        if hay("martina_acepto_resonancia") and not hay("martina_rechazo_resonancia"):
            return "martina_patrocinada"
        for quien in ("claudia", "martina", "rodrigo"):
            if hay("visita_" + quien) and afinidad.get(quien, 0) >= 1:
                return quien
        if afinidad.get("martina", 0) >= 2:
            return "martina"
        if afinidad.get("claudia", 0) >= 3:
            return "claudia"
        return None

    # Reposts necesarios para perder la Gran Viralizacion (por defecto 15000): mas alto, mas facil.
    UMBRAL_ALIADO = {"tomas": 18500, "claudia": 17000, "martina": 17000, "rodrigo": 17000,
                     "martina_patrocinada": 13000}

    # Ganar el Duelo de Frecuencias limpia la senal: el rumor necesita mas reposts para hacerse viral.
    BONO_DUELO = 1500

    def ajustes_viral(base=None):
        ajustes = dict(base or {})
        aliado = aliado_domingo()
        umbral = UMBRAL_ALIADO[aliado] if aliado else None
        if hay("duelo_ganado"):
            umbral = (umbral or 15000) + BONO_DUELO
        if umbral:
            ajustes["umbral_viral"] = umbral
        return ajustes or None


default persistent.avisos_sonido = False

screen aviso_sonido(texto):
    zorder 300
    frame at notificacion_entrada:
        xalign 0.98
        ypos 110
        background Frame(Solid("#1b1426e8"), 0, 0)
        padding (18, 10)
        hbox:
            spacing 10
            text "SONIDO" size 16 bold True color "#facc15" yalign 0.5
            text texto size 22 bold True color "#fbf6ee" yalign 0.5
    timer 2.2 action Hide("aviso_sonido")
