## Expediente: fichas de investigacion. Solo muestra lo que el jugador encontro;
## las relaciones apuntan unicamente a fichas ya obtenidas.

screen exp_chip(estado):
    $ etiqueta, color = inv.ESTADOS_PISTA[estado]
    frame:
        background Solid(color)
        padding (12, 4)
        text etiqueta size 15 bold True color "#ffffff"

screen expediente():
    modal True
    zorder 102
    default nuevas = list(mem()["pistas_nuevas"])
    default seleccion = (list(mem()["pistas_nuevas"]) or list(mem()["pistas"]) or [None])[-1]
    on "show" action [Function(marcar_expediente_visto), Hide("notify")]
    key "game_menu" action Hide("expediente")

    $ propias = mem()["pistas"]
    $ abiertas = sum(1 for p in propias if propias[p] in ("observado", "hipotesis") and inv.PISTAS[p]["preguntas"])

    add Solid("#120d1cd9")
    frame:
        xalign 0.5
        ypos 26
        xysize (1560, 1030)
        background Frame("gui/frame.png", 30, 30)
        padding (40, 30)

        vbox:
            spacing 12
            hbox:
                xfill True
                vbox:
                    text "EXPEDIENTE" size 42 bold True color "#8c2f4b" kerning 4
                    text inv.resumen_investigacion(memoria) size 21 italic True color "#5b4f72"
                vbox:
                    xalign 1.0
                    spacing 8
                    textbutton "CERRAR (Esc)":
                        style "net_boton"
                        text_style "net_boton_text"
                        action Hide("expediente")
                    text ("Hilos abiertos: %d" % abiertas) size 17 color "#8b84a8" xalign 1.0

            hbox:
                spacing 30
                viewport:
                    xsize 470
                    ysize 860
                    mousewheel True
                    scrollbars "vertical"
                    vscrollbar_unscrollable "hide"
                    vbox:
                        spacing 6
                        if not propias:
                            text "Todavía no hay fichas. Revisa CivitasNet y escucha a la gente: las pistas aparecen al inspeccionar." size 20 color "#5b4f72"
                        for categoria in inv.CATEGORIAS_PISTA:
                            $ fichas = [p for p in propias if inv.PISTAS[p]["categoria"] == categoria]
                            if fichas:
                                null height 8
                                text inv.NOMBRE_CATEGORIA[categoria].upper() size 15 bold True color "#8c2f4b" kerning 3
                                for pid in fichas:
                                    button:
                                        xfill True
                                        background ("#efe4f4" if seleccion == pid else "#fbf6ee00")
                                        hover_background "#e6dcf0"
                                        padding (14, 10)
                                        hover_sound "assets/audio/sfx/ui_hover.wav"
                                        action SetScreenVariable("seleccion", pid)
                                        hbox:
                                            spacing 10
                                            add Solid(inv.ESTADOS_PISTA[propias[pid]][1], xysize=(8, 30)) yalign 0.5
                                            text inv.PISTAS[pid]["titulo"] size 20 color "#2b2440" yalign 0.5 xmaximum 330
                                            if pid in nuevas:
                                                text "NUEVA" size 13 bold True color "#e86a7e" yalign 0.5

                frame:
                    xsize 960
                    ysize 860
                    background Solid("#fffaf3")
                    padding (36, 30)
                    if seleccion and seleccion in propias:
                        $ ficha = inv.PISTAS[seleccion]
                        vbox:
                            spacing 14
                            text ficha["titulo"] size 34 bold True color "#2b2440"
                            text "%s  ·  %s  ·  %s" % (inv.NOMBRE_CATEGORIA[ficha["categoria"]], ficha["procedencia"], inv.NOMBRE_MOMENTO[ficha["momento"]]) size 17 color "#8b84a8"
                            use exp_chip(propias[seleccion])
                            text inv.contenido_pista(seleccion, memoria) size 24 color "#2b2440" substitute False
                            if ficha["preguntas"] and propias[seleccion] in ("observado", "hipotesis"):
                                null height 4
                                text "PREGUNTAS ABIERTAS" size 15 bold True color "#d97706" kerning 2
                                for pregunta in ficha["preguntas"]:
                                    text "–  " + pregunta size 20 color "#5b4f72"
                            $ relacionadas = inv.relaciones_conocidas(seleccion, memoria)
                            if relacionadas:
                                null height 4
                                text "SE CONECTA CON" size 15 bold True color "#5b5bd6" kerning 2
                                hbox:
                                    spacing 12
                                    box_wrap True
                                    for rid in relacionadas:
                                        textbutton inv.PISTAS[rid]["titulo"]:
                                            background "#e6e3fb"
                                            hover_background "#cfcaf7"
                                            padding (14, 8)
                                            text_size 18
                                            text_color "#2b2440"
                                            action SetScreenVariable("seleccion", rid)
                    else:
                        text "Elige una ficha." size 22 color "#8b84a8"
