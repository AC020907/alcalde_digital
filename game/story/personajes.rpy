## Elenco, retratos, expresiones y presencia en escena.
## Arte por expresion (en orden de prioridad):
##   images/personajes/sprites/<nombre>_<expresion>.png          -> sprite transparente de escena
##   images/personajes/<nombre>_<expresion>.png                  -> panel enmarcado anterior (respaldo)
##   images/personajes/sprites/lado/<nombre>_<expresion>_lado.png -> retrato junto al dialogo
##   images/personajes/lateral/<nombre>_<expresion>_lado.png     -> retrato historico (CivitasNet, respaldo)
## Si falta todo se usa el retrato base circular con un tratamiento de color.
## Los seis sprites de un personaje comparten lienzo, linea inferior y centro del torso,
## asi que cambiar de expresion no mueve la figura.

init -5 python:
    import math

    PERSONAJES = ["claudia", "martina", "rodrigo", "nova", "tomas"]
    EXPRESIONES = ["neutral", "feliz", "seria", "enojada", "triste", "sorprendida"]

    TRATAMIENTO = {
        "neutral":     None,
        "feliz":       BrightnessMatrix(0.06) * SaturationMatrix(1.2),
        "seria":       SaturationMatrix(0.8) * BrightnessMatrix(-0.03),
        "enojada":     TintMatrix("#ffb8b0") * SaturationMatrix(1.25),
        "triste":      SaturationMatrix(0.45) * BrightnessMatrix(-0.1),
        "sorprendida": BrightnessMatrix(0.1),
    }

    ZOOM_PANEL = 0.88

    # Los sprites son bustos cortados a la altura del pecho. Se apoyan detras de la caja de
    # dialogo (linea base) con un fundido inferior, asi el corte nunca se ve y la cara queda
    # por encima del texto. (lienzo de referencia en px, zoom, linea base y); el fundido usa el
    # tamano real del PNG. La linea base nivela los ojos; NOVA es mas bajito a proposito.
    ENCUADRE_SPRITE = {
        "claudia": ((578, 546), 1.32, 945),
        "martina": ((576, 547), 1.32, 962),
        "rodrigo": ((560, 544), 1.32, 935),
        "tomas":   ((542, 549), 1.32, 940),
        "nova":    ((558, 527), 1.12, 955),
    }

    def retrato_base(nombre, expresion, lado):
        base = "images/personajes/%s_base.png" % nombre
        matriz = TRATAMIENTO.get(expresion)
        if matriz is None:
            return Transform(base, xysize=(lado, lado))
        return Transform(base, xysize=(lado, lado), matrixcolor=matriz)

    # Luz de escena segun el fondo visible: los sprites estan iluminados de dia y sin esto
    # parecen recortes pegados sobre la noche o sobre la red de NOVA.
    LUZ_FONDO = {
        ("ciudad", "noche"): TintMatrix("#c4c8ff") * BrightnessMatrix(-0.05),
        ("civitas",): TintMatrix("#cfd2ff") * BrightnessMatrix(-0.03),
        ("viral",): TintMatrix("#ffd2da") * BrightnessMatrix(-0.03),
        ("ciudad", "tarde"): TintMatrix("#ffe4cc"),
    }
    ATENUADO = BrightnessMatrix(-0.08) * SaturationMatrix(0.75)

    def luz_actual():
        return LUZ_FONDO.get(tuple(renpy.get_attributes("bg") or ()))

    def linea_base(nombre):
        """Y de la base del personaje: detras de la caja de dialogo para los sprites."""
        if nombre in ENCUADRE_SPRITE and usa_sprite(nombre):
            return ENCUADRE_SPRITE[nombre][2]
        return 960

    def usa_sprite(nombre):
        return renpy.loadable("images/personajes/sprites/%s_neutral.png" % nombre)

    def retrato_escena(nombre, expresion):
        sprite = "images/personajes/sprites/%s_%s.png" % (nombre, expresion)
        if renpy.loadable(sprite):
            _, zoom, _ = ENCUADRE_SPRITE[nombre]
            fundido = Transform("gui/fundido_busto.png", xysize=renpy.image_size(sprite))
            return Transform(AlphaMask(sprite, fundido), zoom=zoom)
        panel = "images/personajes/%s_%s.png" % (nombre, expresion)
        if renpy.loadable(panel):
            return Transform(panel, zoom=ZOOM_PANEL)
        return retrato_base(nombre, expresion, 400)

    def retrato_lado(nombre, expresion):
        for ruta in ("images/personajes/sprites/lado/%s_%s_lado.png", "images/personajes/lateral/%s_%s_lado.png"):
            if renpy.loadable(ruta % (nombre, expresion)):
                return ruta % (nombre, expresion)
        return retrato_base(nombre, expresion, 230)

    for _nombre in PERSONAJES:
        renpy.image((_nombre,), retrato_escena(_nombre, "neutral"))
        renpy.image(("side", _nombre), retrato_lado(_nombre, "neutral"))
        for _expr in EXPRESIONES:
            renpy.image((_nombre, _expr), retrato_escena(_nombre, _expr))
            renpy.image(("side", _nombre, _expr), retrato_lado(_nombre, _expr))

    class callback_hablante(object):
        def __init__(self, tag):
            self.tag = tag

        def __call__(self, event, interact=True, **kwargs):
            if event == "begin":
                store.hablante = self.tag

    import time

    class Reacciones(object):
        activas = {}

    def reaccionar(tag, tipo):
        """tipo: 'salto' (alegria), 'temblor' (enojo/shock) o 'sobresalto' (sorpresa)."""
        Reacciones.activas[tag] = (tipo, time.time())

    class funcion_foco(object):
        """El personaje que habla queda iluminado; el resto se atenua y retrocede un poco.
        Incluye entrada, respiracion y reacciones. El anclaje es la linea inferior."""
        def __init__(self, tag, escala=1.0):
            self.tag = tag
            self.escala = escala

        def __call__(self, trans, st, at):
            tag = self.tag
            quieto = persistent.reducir_movimiento
            activo = store.hablante in (None, tag)
            zoom = getattr(self, "escala", 1.0) * (1.0 if activo else 0.97)
            luz = luz_actual()
            if activo:
                trans.matrixcolor = luz
            else:
                trans.matrixcolor = luz * ATENUADO if luz is not None else ATENUADO
            xoffset = 0
            yoffset = 0
            if not quieto:
                yoffset += int(-5 * math.sin(st * 1.1 + len(tag)))
                yoffset += int(24 * (1.0 - min(1.0, st / 0.35)) ** 2)
            reaccion = Reacciones.activas.get(tag)
            if reaccion:
                tipo, inicio = reaccion
                dt = time.time() - inicio
                if dt > 0.45:
                    del Reacciones.activas[tag]
                elif tipo == "salto":
                    yoffset -= int(28 * math.sin(math.pi * min(1.0, dt / 0.32)))
                elif tipo == "temblor":
                    xoffset = int(11 * math.sin(dt * 70) * (1 - dt / 0.45))
                elif tipo == "sobresalto":
                    zoom *= 1.0 + 0.09 * max(0.0, 1 - dt / 0.3)
            trans.zoom = zoom
            trans.xoffset = xoffset
            trans.yoffset = yoffset
            trans.alpha = min(1.0, st / 0.3)
            return 0

    def subir_afinidad(personaje, cantidad, aviso=True):
        store.afinidad[personaje] = store.afinidad.get(personaje, 0) + cantidad
        if aviso:
            texto = ("%s recordará esto." if cantidad > 0 else "%s no olvidará esto.") % NOMBRE_PERSONAJE[personaje]
            renpy.notify(texto)

    NOMBRE_PERSONAJE = {"claudia": "Claudia", "martina": "Martina", "rodrigo": "Rodrigo", "nova": "NOVA", "tomas": "Tomás"}


default hablante = None
default afinidad = {"claudia": 0, "martina": 0, "rodrigo": 0}

image ctc_flecha:
    "gui/ctc.png"
    xpos 1612
    ypos 1018
    block:
        easein 0.45 yoffset 6
        easeout 0.45 yoffset 0
        repeat

define base_personaje = Character(None, ctc="ctc_flecha", ctc_position="fixed",
                                  callback=callback_hablante(None))

define narrator = Character(None, kind=base_personaje, what_italic=False)
define tu = Character("Tú", kind=base_personaje, callback=callback_hablante(None),
                      what_color="#2b2440")
define c = Character("Claudia", kind=base_personaje, image="claudia",
                     callback=callback_hablante("claudia"),
                     namebox_background=Frame("gui/namebox_claudia.png", 34, 10))
define m = Character("Martina", kind=base_personaje, image="martina",
                     callback=callback_hablante("martina"),
                     namebox_background=Frame("gui/namebox_martina.png", 34, 10))
define r = Character("Rodrigo", kind=base_personaje, image="rodrigo",
                     callback=callback_hablante("rodrigo"),
                     namebox_background=Frame("gui/namebox_rodrigo.png", 34, 10))
define t = Character("Tomás Vega", kind=base_personaje, image="tomas",
                     callback=callback_hablante("tomas"),
                     namebox_background=Frame("gui/namebox_tomas.png", 34, 10))
define n = Character("NOVA", kind=base_personaje, image="nova",
                     callback=callback_hablante("nova"),
                     namebox_background=Frame("gui/namebox_nova.png", 34, 10),
                     what_color="#8c2f4b", what_slow_cps=70)
define civitas = Character("CIVITAS", kind=base_personaje,
                           namebox_background=Frame("gui/namebox_nova.png", 34, 10),
                           what_color="#5b4f72")

## ---------------- Posiciones y reacciones ----------------

## x es el centro del personaje en fraccion de pantalla. Posiciones de referencia:
##   solo: 0.5   |   dos: 0.28 y 0.72   |   tres: 0.17, 0.5 y 0.83 con escala 0.84
transform escena(tag, x=0.5, escala=1.0):
    xpos x
    xanchor 0.5
    ypos linea_base(tag)
    yanchor 1.0
    function funcion_foco(tag, escala)

## Cambiar de expresion con un atributo de dialogo ("c feliz ...") funde en vez de cortar.
define config.say_attribute_transition = Dissolve(0.12)

## Transiciones con nombre propio para dar ritmo.
define rapido = Dissolve(0.15)
define suave = Dissolve(0.45)
define lento = Dissolve(1.2)
define negro = Fade(0.6, 0.4, 0.6)
define destello = Fade(0.05, 0.0, 0.35, color="#ffffff")
