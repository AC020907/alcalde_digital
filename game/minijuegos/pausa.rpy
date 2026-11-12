## Pausa comun de los minijuegos de tiempo real (Moderacion, Caza-Rumores, Rastreador).
## Mientras minijuego_pausado es True el reloj de cada minijuego no avanza. El Duelo y la Ruta de la Verdad
## tienen su propia pausa (la cancion y la fisica necesitan detenerse a su manera).

default minijuego_pausado = False

init python:
    def pausar_minijuego():
        store.minijuego_pausado = True
        renpy.show_screen("pausa_minijuego")
        renpy.restart_interaction()

    def reanudar_minijuego():
        store.minijuego_pausado = False
        renpy.hide_screen("pausa_minijuego")
        renpy.restart_interaction()

screen boton_pausa_minijuego(activo=True):
    zorder 60
    if activo and not minijuego_pausado:
        textbutton "Pausa" style "boton_vn_compacto" text_style "boton_vn_text" xalign 0.99 yalign 0.01 action Function(pausar_minijuego)
        key "civ_pausa" action Function(pausar_minijuego)

screen pausa_minijuego():
    modal True
    zorder 200
    add Solid("#000000b8")
    frame:
        align (0.5, 0.5)
        background Frame("gui/frame.png", 30, 30)
        padding (56, 40)
        vbox:
            spacing 16
            text "PAUSA" size 44 bold True color "#2b2440" xalign 0.5
            text "El tiempo está detenido." size 22 color "#5b4f72" xalign 0.5
            textbutton "Continuar" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(reanudar_minijuego) default_focus True
    key "civ_pausa" action Function(reanudar_minijuego)
