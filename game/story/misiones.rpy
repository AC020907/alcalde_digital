## MISIONES PRINCIPALES: que debe hacer el jugador y a que lugar del mapa ir.
## El catalogo y el estado viven en clases/Misiones.py. La historia marca cada mision
## con completar_mision("id"); la activa es siempre la siguiente sin completar.
## El mapa (story/mapa.rpy) marca su destino con un aro amarillo.

default misiones_hechas = []

init python:
    from clases import Misiones as misiones

    def completar_mision(mision_id):
        if mision_id in misiones.POR_ID and mision_id not in store.misiones_hechas:
            store.misiones_hechas.append(mision_id)

    def misiones_pendientes_hud():
        """Insignia del HUD: 1 mientras haya una mision por cumplir."""
        return 1 if misiones.mision_activa(store.misiones_hechas, store.modo_feria_activo) else 0


style mision_texto is default:
    color "#fbf6ee"

screen mision_tarjeta(mision, estado):
    $ hecha = estado == "hecha"
    $ activa = estado == "activa"
    $ color = "#facc15" if activa else ("#7dd3a8" if hecha else "#6b6384")
    $ lugar = UBICACIONES[mision["ubicacion"]][0]
    $ minijuego = mision["minijuego"] or ""
    frame:
        xfill True
        padding (24, 16)
        background Solid("#1d1630f2" if activa else "#171123e6")
        hbox:
            spacing 20
            fixed:
                xsize 44
                ysize 44
                yalign 0.5
                add Solid(color) xsize 44 ysize 44
                text ("✓" if hecha else ("!" if activa else "·")) size 30 bold True color "#120d1c" align (0.5, 0.5)
            vbox:
                spacing 4
                xsize 1100
                text mision["titulo"] size 26 bold True color (color if not hecha else "#c9b8d8")
                text mision["descripcion"] size 18 color ("#6b6384" if estado == "bloqueada" else "#c9b8d8")
                hbox:
                    spacing 24
                    text "Lugar: [lugar]" size 17 bold True color "#a7a5f2"
                    if minijuego:
                        text "Minijuego: [minijuego]" size 17 bold True color "#e86a7e"
            if activa:
                textbutton "Ver en el mapa":
                    yalign 0.5
                    xsize 200
                    ysize 44
                    background Frame("gui/telefono_boton.png", 30, 30)
                    hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                    text_size 16
                    text_bold True
                    text_color "#fbf6ee"
                    text_xalign 0.5
                    text_yalign 0.5
                    hover_sound "assets/audio/sfx/ui_hover.wav"
                    activate_sound "assets/audio/sfx/ui_click.wav"
                    action [Hide("misiones_ciudad"), Function(abrir_mapa_libre)]

screen misiones_ciudad():
    zorder 102
    modal True
    key "game_menu" action Hide("misiones_ciudad")
    add Solid("#120d1cd9")
    frame:
        xysize (1560, 1030)
        xalign 0.5
        ypos 26
        padding (40, 32)
        background Solid("#120d1cf2")
        vbox:
            spacing 16
            hbox:
                xfill True
                vbox:
                    text "DIARIO" size 16 color "#a7a5f2" kerning 3
                    text "Misiones principales" size 40 bold True style "mision_texto"
                textbutton "Cerrar":
                    xalign 1.0
                    yalign 0.5
                    xsize 138
                    ysize 44
                    background Frame("gui/telefono_boton.png", 30, 30)
                    hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                    text_size 16
                    text_bold True
                    text_color "#fbf6ee"
                    text_xalign 0.5
                    text_yalign 0.5
                    action Hide("misiones_ciudad")
            viewport:
                mousewheel True
                scrollbars "vertical"
                ysize 850
                vbox:
                    spacing 12
                    xfill True
                    for mision, estado in misiones.estado_misiones(misiones_hechas, modo_feria_activo):
                        use mision_tarjeta(mision, estado)
