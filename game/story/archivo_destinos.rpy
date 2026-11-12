## Archivo de Destinos: los finales como coleccionables. Los no descubiertos guardan el misterio.

transform destino_entrada(retraso):
    alpha 0.0 yoffset 24
    pause retraso
    easein 0.35 alpha 1.0 yoffset 0

transform destino_destacado:
    block:
        easein 0.8 zoom 1.03
        easeout 0.8 zoom 1.0
        repeat

screen tarjeta_destino(final, retraso=0.0, destacar=None):
    $ d = destinos.DESTINOS[final]
    $ visto = final in persistent.finales_vistos
    frame:
        xysize (300, 470)
        background Frame("gui/frame.png", 30, 30)
        padding (22, 26)
        at (destino_destacado if (final == destacar and not persistent.reducir_movimiento) else destino_entrada(retraso))
        has vbox
        spacing 14
        xfill True
        fixed:
            xysize (120, 120)
            xalign 0.5
            add circulo(d["color"] if visto else "#cfc8de", "#fbf6ee", 60) align (0.5, 0.5)
            text (d["insignia"][0] if visto else "?") size 64 bold True color "#fbf6ee" align (0.5, 0.5)
        if visto:
            text d["titulo"] size 28 bold True color "#2b2440" xalign 0.5 text_align 0.5
            text d["insignia"] size 18 color d["color"] xalign 0.5 kerning 3
            text d["descripcion"] size 19 color "#5b4f72" text_align 0.5 xalign 0.5
        else:
            text "Destino oculto" size 28 bold True color "#8b84a8" xalign 0.5
            text "PISTA" size 18 color "#8b84a8" xalign 0.5 kerning 3
            text d["misterio"] size 19 italic True color "#8b84a8" text_align 0.5 xalign 0.5

screen archivo_destinos(destacar=None):
    modal True
    zorder 130
    key "game_menu" action Hide("archivo_destinos")
    add Solid("#1b1426ee")
    vbox:
        align (0.5, 0.5)
        spacing 30
        text "ARCHIVO DE DESTINOS" size 46 bold True color "#fbf6ee" xalign 0.5 kerning 4
        text ("Has descubierto %d de %d destinos de Ciudad Nova" % (len(finales_descubiertos()), len(destinos.FINALES))) size 24 color "#a7a5f2" xalign 0.5
        hbox:
            spacing 26
            xalign 0.5
            for i, final in enumerate(destinos.FINALES):
                use tarjeta_destino(final, 0.08 * i, destacar)
        textbutton "CERRAR":
            style "boton_vn"
            text_style "boton_vn_text"
            xalign 0.5
            action Hide("archivo_destinos")
            default_focus True
