## Puesta en escena: fondos, camara, tarjetas de lugar y efectos.

image bg ciudad = "images/bg/ciudad_dia.jpg"
image bg ciudad tarde = "images/bg/ciudad_tarde.jpg"
image bg ciudad noche = "images/bg/ciudad_noche.jpg"
image bg alcaldia = "images/bg/alcaldia.jpg"
image bg panorama = "images/bg/panorama.jpg"
image bg despacho = "images/bg/despacho.jpg"
image bg redaccion = "images/bg/redaccion.jpg"
image bg operaciones = "images/bg/operaciones.jpg"
image bg estudio_martina = "images/bg/estudio_martina.jpg"
image bg barrio_centro = "images/bg/barrio_centro.jpg"
image bg barrio_prensa = "images/bg/barrio_prensa.jpg"
image bg barrio_sur = "images/bg/barrio_sur.jpg"
## Los fondos de barrio son vistas aereas: sirven de plano de establecimiento. Para
## conversar se desenfocan (profundidad de campo) y el personaje queda en primer plano.
image bg barrio_sur conversacion = Transform("images/bg/barrio_sur.jpg", blur=7,
                                            matrixcolor=SaturationMatrix(0.85) * BrightnessMatrix(-0.03))
image bg civitas = "assets/backgrounds/fondo_rastreador.jpg"
image bg crisis = "assets/backgrounds/fondo_contencion.jpg"
image bg viral = "assets/backgrounds/fondo_viralizacion.jpg"
image bg mapa = "images/bg/mapa.jpg"
image negro = Solid("#000000")

## Camara lenta sobre el fondo (desactivada con "Reducir movimiento").
init python:
    def funcion_paneo(trans, st, at):
        if persistent.reducir_movimiento:
            trans.zoom = 1.0
            trans.xoffset = 0
            return None
        ciclo = (math.sin(st / 9.0) + 1) / 2
        trans.zoom = 1.03 + 0.03 * ciclo
        trans.xoffset = int(-30 * ciclo)
        return 0

transform paneo:
    xalign 0.5
    yalign 0.5
    function funcion_paneo

## Plano de establecimiento: desplazamiento sobre el mapa ilustrado de la ciudad.
transform sobre_mapa(x0, y0, x1, y1, duracion=6.0):
    xanchor 0.0 yanchor 0.0
    xpos x0 ypos y0
    ease duracion xpos x1 ypos y1

transform zoom_dramatico:
    zoom 1.0
    easein 3.0 zoom 1.12

## Tarjeta de lugar y hora (entra, se queda un momento y se va).
transform tarjeta_lugar_anim:
    alpha 0.0 xoffset -40
    easein 0.45 alpha 1.0 xoffset 0
    pause 2.2
    easeout 0.5 alpha 0.0 xoffset -20

screen tarjeta_lugar(dia, lugar):
    zorder 30
    frame at tarjeta_lugar_anim:
        xpos 60
        ypos 60
        background Frame("gui/frame.png", 30, 30)
        padding (34, 18, 40, 20)
        vbox:
            spacing 2
            text dia size 18 bold True color "#8c2f4b" kerning 3
            text lugar size 32 bold True color "#2b2440"
    timer 3.4 action Hide("tarjeta_lugar")

## Titulo de acto a pantalla completa.
transform titulo_acto_anim:
    alpha 0.0 yoffset 20
    easein 0.8 alpha 1.0 yoffset 0

screen titulo_acto(numero, titulo, subtitulo):
    add Solid("#1b1426")
    vbox at titulo_acto_anim:
        align (0.5, 0.5)
        spacing 14
        text numero size 26 bold True color "#e86a7e" xalign 0.5 kerning 6
        text titulo size 74 bold True color "#fbf6ee" xalign 0.5
        text subtitulo size 28 color "#c9b8d8" xalign 0.5
    timer 3.2 action Return()
    key "dismiss" action Return()

## Interferencia de NOVA: franjas y desplazamiento de color durante un instante.
transform glitch_franja(y, alto, desfase):
    ypos y
    xoffset 0
    alpha 0.0
    pause desfase
    alpha 0.85
    linear 0.05 xoffset 40
    linear 0.05 xoffset -60
    linear 0.05 xoffset 20
    alpha 0.0

screen glitch():
    zorder 90
    for i, (y, alto, color, desfase) in enumerate([(120, 26, "#ff2a5580", 0.0), (380, 12, "#2ad4ff70", 0.05),
                                                     (610, 40, "#ff2a5560", 0.1), (840, 18, "#ffffff50", 0.02),
                                                     (250, 8, "#2ad4ff80", 0.12), (950, 30, "#ff2a5570", 0.07)]):
        add Solid(color, xsize=1920, ysize=alto) at glitch_franja(y, alto, desfase)
    timer 0.5 action Hide("glitch")

init python:
    def interferencia():
        renpy.show_screen("glitch")
        sonar(SONIDO_AVISO["alerta"])


## Boton crema para la interfaz de novela (no la de Civitas).
style boton_vn is default:
    background "gui/boton_menu_idle.png"
    hover_background "gui/boton_menu_hover.png"
    xysize (406, 86)
    hover_sound "assets/audio/sfx/ui_hover.wav"
    activate_sound "assets/audio/sfx/ui_click.wav"

style boton_vn_text is default:
    size 26
    bold True
    color "#2b2440"
    xalign 0.5
    yalign 0.42
