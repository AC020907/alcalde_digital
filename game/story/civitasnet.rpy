## CivitasNet: la red social de Ciudad Nova. El feed se deriva del estado (memoria);
## ninguna pantalla guarda publicaciones propias.
## Uso narrativo:  call abrir_civitasnet("net_memo_salud")   (destaca una publicacion)
## Desde el HUD se abre sin bloquear la historia.
##
## Diseno: Figma "CivitasNet - UI estilo Instagram" (feed e inspeccionar), a escala NET_Z.
## Imagenes de apoyo y iconos SVG en images/civitasnet/.

init python:

    NET_Z = 1.25                     # el Figma es de 540 px de ancho; en el juego se ve a esta escala

    def nz(n):
        return int(round(n * NET_Z))

    NET_ANCHO = nz(540)              # ancho del telefono
    NET_ALTO = 1040
    NET_INT = NET_ANCHO - 4          # ancho util, sin el borde de 2 px
    NET_H_SUP = nz(61)               # barra superior del feed
    NET_H_HIST = nz(105)             # fila de historias
    NET_H_DET = nz(54)               # barra superior de la vista inspeccionar
    NET_H_NAV = nz(70)               # navegacion inferior (incluye su linea)
    NET_RUTA = "images/civitasnet/%s"

    def net_icono(nombre):
        return NET_RUTA % (nombre + ".svg")

    # Color del avatar de letra: personajes fijos; el resto segun el tipo (los bots se ven como ciudadanos).
    NET_COLOR_PERSONAJE = {"@claudia.reporta": "2f9e8f", "@martina.sol": "d6779a", "@tienda.rodrigo": "b8860b",
                           "@tomas.vega": "7c7cf0", "@n0va": "e04f5f"}
    NET_COLOR_TIPO = {"medio": "5b5bd6", "institucion": "7c7cf0", "ciudadano": "2f9e8f", "influencer": "d6779a",
                      "bot": "2f9e8f", "publicidad": "b8860b", "personaje": "6b5fa0", "nova": "e04f5f"}

    # Historias: (letra, nombre, color), tal como en el diseno.
    NET_HISTORIAS = [("A", "Tu alcaldía", "5b5bd6"), ("C", "claudia", "2f9e8f"), ("M", "martina", "d6779a"),
                     ("R", "rodrigo", "b8860b"), ("T", "tomas", "7c7cf0")]

    NET_HEROES = ("pendiente", "verificada", "cuestionada", "manipulada", "publicidad")
    NET_CHIPS = {"pendiente": ("PENDIENTE", "#b8860b")}

    def net_color_avatar(post):
        return NET_COLOR_PERSONAJE.get(post["autor"]) or NET_COLOR_TIPO.get(post["tipo"], "2f9e8f")

    def net_inicial(autor):
        return autor.lstrip("@")[:1].upper() or "?"

    def net_chip_datos(estado):
        return NET_CHIPS.get(estado) or inv.ESTADOS_POST[estado]

    def net_tam_hero(texto):
        n = len(texto)
        return nz(26) if n <= 70 else (nz(22) if n <= 120 else nz(19))

    def cerrar_civitasnet(llamada):
        return Return() if llamada else Hide("civitasnet")


style net_scroll is vscrollbar:
    xsize 8
    base_bar Solid("#2f2744")
    thumb Solid("#a7a5f2")
    unscrollable "hide"

## ----- piezas -----

screen net_avatar(color, letra, lado, tam):
    fixed:
        xysize (lado, lado)
        add Transform(NET_RUTA % "circ_grad.png", xysize=(lado, lado))
        add Transform(NET_RUTA % "circ_fondo.png", xysize=(lado - 6, lado - 6), align=(0.5, 0.5))
        add Transform(NET_RUTA % ("circ_" + color + ".png"), xysize=(lado - 10, lado - 10), align=(0.5, 0.5))
        text letra size tam bold True color "#ffffff" align (0.5, 0.5)

screen net_chip(estado):
    $ etiqueta, color = net_chip_datos(estado)
    frame:
        background Solid(color)
        padding (nz(8), nz(3))
        yalign 0.5
        text etiqueta size nz(11) bold True color "#ffffff"

## Una publicacion tal como en el Figma: cabecera, imagen, acciones y datos.
## No hay imagenes en las publicaciones del juego: el texto va dentro de la imagen.
screen net_post(post, nueva=False):
    $ estado = inv.estado_post(post, memoria)
    $ nova = post["tipo"] == "nova"
    $ texto = inv.texto_post(post, memoria)
    $ fondo = NET_RUTA % ("hero_%s.png" % (estado if estado in NET_HEROES else "pendiente"))
    vbox:
        xfill True
        frame:
            background None
            xfill True
            padding (nz(16), nz(12))
            fixed:
                ysize nz(46)
                hbox:
                    spacing nz(10)
                    yalign 0.5
                    use net_avatar(net_color_avatar(post), net_inicial(post["autor"]), nz(46), nz(19))
                    vbox:
                        yalign 0.5
                        spacing 1
                        text post["autor"] size nz(14) bold True color ("#ff8fa3" if nova else "#fbf6ee") substitute False
                        text "Ciudad Nova · " + post["hora"] size nz(12) color "#a99fc4" substitute False
                hbox:
                    xalign 1.0
                    yalign 0.5
                    spacing nz(10)
                    if nueva:
                        text "NUEVA" size nz(11) bold True color "#facc15" yalign 0.5
                    use net_chip(estado)
                    add net_icono("mas") yalign 0.5
        fixed:
            xfill True
            ysize nz(190)
            add Transform(fondo, xysize=(NET_INT, nz(190)))
            text texto size net_tam_hero(texto) bold True color "#ffffff" xalign 0.5 yalign 0.5 text_align 0.5 xsize (NET_INT - nz(64)) substitute False
        frame:
            background None
            xfill True
            padding (nz(16), nz(12))
            fixed:
                ysize nz(24)
                hbox:
                    spacing nz(16)
                    add net_icono("corazon")
                    add net_icono("comentario")
                    add net_icono("repost")
                    add net_icono("enviar")
                add net_icono("guardar") xalign 1.0
        frame:
            background None
            xfill True
            padding (nz(16), 0, nz(16), nz(16))
            vbox:
                spacing nz(6)
                text "%s %s  ·  %s me gusta" % (formato_num(post["reposts"]), "repost" if post["reposts"] == 1 else "reposts", formato_num(post["likes"])) size nz(13) bold True color "#fbf6ee" substitute False
                text ("Fuente: " + post["fuente"] if post["fuente"] else "Fuente: ninguna citada") size nz(12) color "#a7a5f2" substitute False

screen net_post_feed(post, nueva):
    button:
        xfill True
        padding (0, 0)
        background None
        hover_background Solid("#ffffff0a")
        hover_sound "assets/audio/sfx/menu_hover.ogg"
        action [SetScreenVariable("seleccion", post["id"]), SetScreenVariable("vista", "detalle")]
        use net_post(post, nueva)

screen net_tarjeta_info(titulo, color, texto):
    frame:
        background None
        xfill True
        padding (nz(16), 0)
        frame:
            xfill True
            background Frame(NET_RUTA % "tarjeta_info.png", 24, 24)
            padding (nz(16), nz(14))
            vbox:
                spacing nz(6)
                text titulo size nz(12) bold True color color kerning 2
                text texto size nz(14) color "#fbf6ee" substitute False

screen net_nav(activa):
    $ columna = (NET_INT - nz(24)) // 5
    $ columnas = [("inicio", "Inicio"), ("buscar", "Buscar"), ("reportar", "Reportar"),
                  ("expediente", "Expediente"), ("perfil", "Perfil")]
    vbox:
        xfill True
        add Solid("#2f2744") xsize NET_INT ysize 1
        frame:
            background None
            xfill True
            ysize NET_H_NAV - 1
            padding (nz(12), nz(14))
            hbox:
                for clave, etiqueta in columnas:
                    $ encendida = clave == activa
                    $ icono = ("nav_%s_%s" % (clave, "on" if encendida else "off")) if clave in ("inicio", "expediente") else "nav_" + clave
                    $ accion = SetScreenVariable("vista", "feed") if clave == "inicio" else (Show("expediente") if clave == "expediente" else None)
                    button:
                        xsize columna
                        background None
                        padding (0, 0)
                        action accion
                        hover_sound ("assets/audio/sfx/menu_hover.ogg" if accion else None)
                        vbox:
                            spacing nz(3)
                            xalign 0.5
                            fixed:
                                xysize (nz(26), nz(26))
                                xalign 0.5
                                add net_icono(icono)
                                if clave == "expediente" and pistas_sin_ver():
                                    frame:
                                        xalign 1.0
                                        xoffset nz(6)
                                        yoffset nz(-4)
                                        background Solid("#e86a7e")
                                        padding (nz(5), 0)
                                        text str(pistas_sin_ver()) size nz(10) bold True color "#ffffff"
                            text etiqueta size nz(10) bold encendida color ("#a7a5f2" if encendida else "#a99fc4") xalign 0.5

## ----- pantallas -----

screen net_feed(nuevos, feed, adj):
    ## barra superior
    frame:
        background None
        xfill True
        ysize NET_H_SUP
        padding (nz(16), 0)
        fixed:
            hbox:
                yalign 0.5
                spacing nz(14)
                text "CIVITAS" size nz(28) bold True color "#a7a5f2" kerning 2 yalign 0.5
                text "Ciudad Nova  ·  " + inv.NOMBRE_MOMENTO[memoria["momento"]] size nz(13) color "#a99fc4" yalign 0.5
            hbox:
                xalign 1.0
                yalign 0.5
                spacing nz(14)
                add net_icono("corazon_top")
                add net_icono("enviar_top")
    ## historias
    frame:
        background None
        xfill True
        ysize NET_H_HIST
        padding (nz(16), nz(10))
        hbox:
            spacing nz(16)
            for letra, nombre, color in NET_HISTORIAS:
                vbox:
                    spacing nz(6)
                    xsize nz(66)
                    use net_avatar(color, letra, nz(66), nz(24))
                    text nombre size nz(11) color "#fbf6ee" xalign 0.5
    add Solid("#2f2744") xsize NET_INT ysize 1
    $ alto = NET_ALTO - 4 - NET_H_SUP - NET_H_HIST - 1 - NET_H_NAV
    hbox:
        viewport:
            xsize (NET_INT - 8)
            ysize alto
            yadjustment adj
            mousewheel True
            draggable True
            vbox:
                xfill True
                for post in feed:
                    use net_post_feed(post, post["id"] in nuevos)
                    add Solid("#2f2744") xsize (NET_INT - 8) ysize 1
        vbar adjustment adj style "net_scroll" ysize alto
    use net_nav("inicio")

screen net_inspeccionar(post, adj):
    $ estado = inv.estado_post(post, memoria)
    $ pendiente = estado == "pendiente"
    $ fuente = (post["fuente"] or "No cita ninguna fuente.") + (" Nadie la ha verificado todavía." if pendiente and not post["fuente"] else "")
    $ contexto = post["contexto"] or ("Que sea popular no la vuelve cierta: %s reposts no son evidencia." % formato_num(post["reposts"]) if pendiente else None)
    frame:
        background None
        xfill True
        ysize NET_H_DET
        padding (nz(16), 0)
        fixed:
            hbox:
                yalign 0.5
                spacing nz(12)
                imagebutton:
                    idle net_icono("volver")
                    hover_sound "assets/audio/sfx/menu_hover.ogg"
                    action SetScreenVariable("vista", "feed")
                    yalign 0.5
                text "Publicación" size nz(18) bold True color "#fbf6ee" yalign 0.5
            add net_icono("escudo") xalign 1.0 yalign 0.5
    $ alto = NET_ALTO - 4 - NET_H_DET - NET_H_NAV
    hbox:
      viewport:
        xsize (NET_INT - 8)
        ysize alto
        yadjustment adj
        mousewheel True
        draggable True
        vbox:
            xfill True
            spacing nz(12)
            use net_post(post)
            use net_tarjeta_info("FUENTE", "#a7a5f2", fuente)
            if contexto:
                use net_tarjeta_info("CONTEXTO", "#facc15", contexto)
            if post["pista"]:
                frame:
                    background None
                    xfill True
                    padding (nz(16), 0, nz(16), nz(16))
                    if tiene_pista(post["pista"]):
                        text "Ya está en tu expediente." size nz(15) bold True color "#7ee0c3" xalign 0.5
                    else:
                        button:
                            xfill True
                            ysize nz(52)
                            background Frame(NET_RUTA % "boton_expediente.png", 24, 24)
                            hover_foreground Solid("#ffffff1f")
                            hover_sound "assets/audio/sfx/menu_hover.ogg"
                            activate_sound "assets/audio/sfx/decision.ogg"
                            action Function(dar_pista, post["pista"])
                            hbox:
                                align (0.5, 0.5)
                                spacing nz(10)
                                add net_icono("carpeta_boton") yalign 0.5
                                text "AÑADIR AL EXPEDIENTE" size nz(15) bold True color "#ffffff" yalign 0.5
      vbar adjustment adj style "net_scroll" ysize alto
    use net_nav("expediente")

screen civitasnet(llamada=False, destacar=None):
    modal True
    zorder 101
    default nuevos = set(inv.posts_nuevos(memoria))
    default seleccion = destacar
    default vista = "detalle" if destacar else "feed"
    default feed_adj = ui.adjustment()
    default det_adj = ui.adjustment()
    on "show" action [Function(marcar_feed_visto), Hide("notify")]
    key "game_menu" action cerrar_civitasnet(llamada)

    $ feed = inv.feed_visible(memoria)
    $ elegido = inv.POSTS_POR_ID.get(seleccion)

    add Solid("#120d1cd9")

    text "Los me gusta no son evidencia.\nAbre una publicación para ver de dónde viene." size 22 color "#c9b8d8" xalign 0.5 xoffset (-(NET_ANCHO // 2 + 200)) yalign 0.5 xsize 340 text_align 0.5

    frame:
        align (0.5, 0.5)
        xysize (NET_ANCHO, NET_ALTO)
        background Frame(NET_RUTA % "marco_telefono.png", 50, 50)
        padding (2, 2)
        vbox:
            xfill True
            if vista == "detalle" and elegido:
                use net_inspeccionar(elegido, det_adj)
            else:
                use net_feed(nuevos, feed, feed_adj)

    textbutton ("CONTINUAR" if llamada else "CERRAR (Esc)"):
        style "net_boton"
        text_style "net_boton_text"
        xalign 0.5
        xoffset (NET_ANCHO // 2 + 160)
        yalign 0.5
        action cerrar_civitasnet(llamada)

style net_boton is default:
    background Frame("gui/telefono_boton.png", 30, 30)
    hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
    padding (26, 14)
    hover_sound "assets/audio/sfx/menu_hover.ogg"

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
