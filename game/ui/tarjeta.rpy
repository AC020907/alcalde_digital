screen civitas_tarjeta(autor, contenido, likes, reposts, avatar="images/placeholder1.png"):
    zorder 40
    frame:
        at (tarjeta_entra if efectos_activos() else tarjeta_fade)
        xalign 0.97 yalign 0.30
        xsize 640
        padding (26, 22)
        background "#0b1220f2"
        vbox:
            spacing 12
            hbox:
                spacing 14
                add Transform(Crop((0, 0, 800, 800), avatar), fit="cover", xysize=(72, 72))
                vbox:
                    text "[autor]" size 28 bold True color "#e2e8f0"
                    text "Civitas · hace unos minutos" size 18 color "#94a3b8"
            text "[contenido]" size 30 color "#f8fafc"
            hbox:
                spacing 28
                text "Me gusta [likes]" size 20 color "#94a3b8"
                text "Compartidos [reposts]" size 20 color "#94a3b8"
            frame:
                background "#78350f" padding (12, 4)
                text "Sin verificar" size 18 color "#fde68a"
