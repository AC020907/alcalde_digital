## CivitasNet: la red social de Ciudad Nova. El feed se deriva del estado (memoria);
## ninguna pantalla guarda publicaciones propias.
## Uso narrativo:  call abrir_civitasnet("net_memo_salud")   (destaca una publicacion)
## Desde el HUD se abre sin bloquear la historia.

init python:

    AVATAR_PERSONAJE = {"@claudia.reporta": "claudia", "@martina.sol": "martina", "@tienda.rodrigo": "rodrigo",
                        "@tomas.vega": "tomas", "@n0va": "nova"}
    AVATAR_TIPO = {"medio": "medio", "institucion": "jugador", "ciudadano": "ciudadano", "influencer": "influencer",
                   "bot": "ciudadano", "publicidad": "medio", "personaje": "ciudadano", "nova": "bot"}

    def avatar_post(post):
        personaje = AVATAR_PERSONAJE.get(post["autor"])
        if personaje:
            return "images/personajes/lateral/%s_neutral_lado.png" % personaje
        return ICONO_TIPO[AVATAR_TIPO.get(post["tipo"], "ciudadano")]

    def cerrar_civitasnet(llamada):
        return Return() if llamada else Hide("civitasnet")


style net_texto is default:
    color "#ece6ff"
    size 22

style net_chip_text is default:
    size 14
    bold True
    color "#ffffff"
    kerning 1

screen net_chip(estado):
    $ etiqueta, color = inv.ESTADOS_POST[estado]
    frame:
        background Solid(color)
        padding (10, 3)
        yalign 0.5
        text etiqueta style "net_chip_text"

screen net_tarjeta(post, seleccionada, nueva):
    $ estado = inv.estado_post(post, memoria)
    $ nova = post["tipo"] == "nova"
    button:
        xfill True
        background Frame("gui/telefono_post.png", 24, 24)
        hover_background Frame("gui/telefono_post.png", 24, 24)
        hover_foreground Solid("#ffffff10")
        selected_foreground Solid("#a7a5f22a")
        selected seleccionada
        padding (22, 18)
        hover_sound "assets/audio/sfx/ui_hover.wav"
        action SetScreenVariable("seleccion", post["id"])
        hbox:
            spacing 16
            add Transform(avatar_post(post), xysize=(58, 58))
            vbox:
                spacing 6
                xsize 720
                hbox:
                    spacing 12
                    text post["autor"] size 21 bold True color ("#ff8fa3" if nova else "#fbf6ee") yalign 0.5
                    text post["hora"] size 15 color "#a99fc4" yalign 0.5
                    use net_chip(estado)
                    if nueva:
                        text "NUEVA" size 14 bold True color "#facc15" yalign 0.5
                text inv.texto_post(post, memoria) style "net_texto" color ("#ffb3c1" if nova else "#ece6ff") substitute False
                if post["fuente"]:
                    text "Fuente: " + post["fuente"] size 16 color "#a7a5f2" substitute False
                text "%s me gusta  ·  %s reposts" % (formato_num(post["likes"]), formato_num(post["reposts"])) size 15 color "#8b84a8"

screen net_detalle(post):
    $ estado = inv.estado_post(post, memoria)
    vbox:
        spacing 14
        text "INSPECCIONAR" size 16 bold True color "#a7a5f2" kerning 3
        hbox:
            spacing 12
            add Transform(avatar_post(post), xysize=(52, 52))
            vbox:
                text post["autor"] size 22 bold True color "#fbf6ee"
                text post["hora"] size 15 color "#a99fc4"
        use net_chip(estado)
        text inv.texto_post(post, memoria) size 21 color "#ece6ff" substitute False
        text "FUENTE" size 15 bold True color "#a7a5f2" kerning 2
        text (post["fuente"] or "No cita ninguna fuente.") size 19 color "#ece6ff" substitute False
        if post["contexto"]:
            text "CONTEXTO" size 15 bold True color "#a7a5f2" kerning 2
            text post["contexto"] size 19 color "#ece6ff" substitute False
        if estado == "pendiente":
            text "Nadie la ha verificado todavía. Que sea popular no la vuelve cierta." size 17 italic True color "#c9b8d8"
        null height 6
        if post["pista"]:
            if tiene_pista(post["pista"]):
                text "Ya está en tu expediente." size 18 bold True color "#7ee0c3"
            else:
                textbutton "AÑADIR AL EXPEDIENTE":
                    xfill True
                    ysize 64
                    background Frame("gui/telefono_boton.png", 30, 30)
                    hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                    text_size 21
                    text_bold True
                    text_color "#fbf6ee"
                    text_xalign 0.5
                    text_yalign 0.5
                    activate_sound "assets/audio/sfx/eleccion.wav"
                    action Function(dar_pista, post["pista"])

screen civitasnet(llamada=False, destacar=None):
    modal True
    zorder 101
    default nuevos = set(inv.posts_nuevos(memoria))
    default seleccion = destacar
    on "show" action [Function(marcar_feed_visto), Hide("notify")]
    key "game_menu" action cerrar_civitasnet(llamada)

    $ feed = inv.feed_visible(memoria)
    $ elegido = inv.POSTS_POR_ID.get(seleccion)

    add Solid("#120d1cd9")
    frame:
        xalign 0.5
        ypos 26
        xysize (1560, 1030)
        background Solid("#241b35")
        padding (34, 26)

        vbox:
            spacing 14
            hbox:
                xfill True
                vbox:
                    text "CivitasNet" size 44 bold True color "#a7a5f2"
                    text "Ciudad Nova  ·  " + inv.NOMBRE_MOMENTO[memoria["momento"]] size 18 color "#a99fc4"
                hbox:
                    xalign 1.0
                    yalign 0.5
                    spacing 14
                    textbutton ("EXPEDIENTE (%d)" % pistas_sin_ver() if pistas_sin_ver() else "EXPEDIENTE"):
                        style "net_boton"
                        text_style "net_boton_text"
                        action Show("expediente")
                    textbutton ("CONTINUAR" if llamada else "CERRAR (Esc)"):
                        style "net_boton"
                        text_style "net_boton_text"
                        action cerrar_civitasnet(llamada)
            text "Los me gusta no son evidencia. Abre una publicación para ver de dónde viene." size 18 color "#c9b8d8"

            hbox:
                spacing 30
                viewport:
                    xsize 880
                    ysize 820
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    vscrollbar_unscrollable "hide"
                    vbox:
                        spacing 12
                        for post in feed:
                            use net_tarjeta(post, seleccion == post["id"], post["id"] in nuevos)
                frame:
                    xsize 570
                    ysize 820
                    background Frame("gui/telefono_post.png", 24, 24)
                    padding (28, 24)
                    if elegido:
                        use net_detalle(elegido)
                    else:
                        text "Elige una publicación para inspeccionar su fuente y su contexto." size 21 color "#c9b8d8" yalign 0.4

style net_boton is default:
    background Frame("gui/telefono_boton.png", 30, 30)
    hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
    padding (26, 14)
    hover_sound "assets/audio/sfx/ui_hover.wav"

style net_boton_text is default:
    size 20
    bold True
    color "#fbf6ee"

label abrir_civitasnet(destacar=None):
    $ ocultar_avisos_juego()
    window hide
    call screen civitasnet(llamada=True, destacar=destacar)
    window auto
    return
