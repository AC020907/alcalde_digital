## Minijuego 2 - Moderador (tiempo real).
## Uso:  call minijuego_moderador             (semilla aleatoria)
##       call minijuego_moderador(semilla=7)  (partida reproducible)

init python:
    from clases.Moderador import ColaModeracion
    from clases.Publicacion import Publicacion

    from clases.moderacion_datos import COMENTARIOS_MODERACION, publicaciones_moderacion


    def avatar_comentario(autor):
        if red_civitas.existe(autor):
            return icono_aparente(red_civitas, autor, False)
        return ICONO_TIPO["ciudadano"]

    def tick_moderacion(cola, dt):
        atendidas = cola.atendidas
        cola.tick(dt)
        if cola.atendidas != atendidas and cola.ultimo:
            sonar(SONIDO_AVISO["bueno" if cola.ultimo[1] else "malo"])
            renpy.hide_screen("moderador_feedback")
            renpy.show_screen("moderador_feedback", texto=cola.ultimo[0], correcto=cola.ultimo[1])
            if cola.terminado():
                sonar(SONIDO_EXITO if cola.exito() else SONIDO_FALLO)

    def moderar(cola, eliminar):
        if cola.decidir(eliminar):
            sonar(SONIDO_AVISO["bueno"])
        else:
            sonar(SONIDO_AVISO["malo"])
        if cola.terminado():
            sonar(SONIDO_EXITO if cola.exito() else SONIDO_FALLO)
        renpy.hide_screen("moderador_feedback")
        renpy.show_screen("moderador_feedback", texto=cola.ultimo[0], correcto=cola.ultimo[1])


transform tarjeta_comentario:
    alpha 0.0 xoffset 260
    easein 0.22 alpha 1.0 xoffset 0

transform feedback_moderador:
    alpha 0.0 zoom 1.4
    easein 0.15 alpha 1.0 zoom 1.0
    pause 0.45
    easeout 0.3 alpha 0.0 yoffset -30

screen moderador_feedback(texto, correcto):
    zorder 120
    text texto at feedback_moderador:
        xalign 0.5
        ypos 300
        size 44
        bold True
        color ("#2f9e8f" if correcto else "#e04f5f")
        outlines [(4, "#fbf6ee", 0, 0)]
    timer 0.95 action Hide("moderador_feedback")

screen moderador_tarjeta(cola, creadas):
    $ com = cola.actual
    frame:
        xalign 0.5
        ypos 380
        xsize 980
        background Frame("gui/frame.png", 30, 30)
        padding (40, 32)
        vbox:
            spacing 16
            hbox:
                spacing 16
                add Transform(avatar_comentario(com.autor), xysize=(78, 78))
                vbox:
                    yalign 0.5
                    text com.autor size 28 bold True color "#2b2440"
                    text "Cuenta creada: " + creadas.get(com.autor, "?") size 18 color "#8b84a8"
            text com.contenido size 30 color "#2b2440"

screen moderador_ui(cola, creadas):
    modal True
    zorder 40

    if not cola.terminado():
        timer 0.05 repeat True action If(minijuego_pausado, NullAction(), Function(tick_moderacion, cola, 0.05))
        use boton_pausa_minijuego
        if cola.jugando():
            key "civ_izq" action Function(moderar, cola, True)
            key "civ_der" action Function(moderar, cola, False)

    add "bg civitas"
    add Solid("#1b1426b0")

    hbox:
        xalign 0.5
        ypos 40
        spacing 70
        vbox:
            text "MODERACIÓN EXPRESS" size 40 bold True color "#fbf6ee"
            text "Borra bots y desinformación. Aprueba a las personas reales, aunque critiquen." size 20 color "#c9b8d8"
        vbox:
            text "PUNTOS" size 16 color "#a7a5f2"
            text formato_num(cola.puntos) size 38 bold True color "#fbf6ee"
        vbox:
            text "VIDAS" size 16 color "#a7a5f2"
            hbox:
                spacing 8
                for i in range(3):
                    add circulo("#e86a7e" if i < cola.vidas else "#3a3350", "#fbf6ee", 14)
        vbox:
            text "EN COLA" size 16 color "#a7a5f2"
            text "[cola.pendientes()]" size 38 bold True color "#fbf6ee"

    if cola.racha >= 3:
        text "RACHA x[cola.racha]" size 34 bold True color "#facc15" xalign 0.5 ypos 170 outlines [(3, "#2b2440", 0, 0)]

    # Al terminar se retiran tarjeta y botones: si no, el mando puede quedarse con el foco en BORRAR/APROBAR.
    if cola.actual is not None and cola.intro <= 0 and not cola.terminado():
        bar:
            xalign 0.5
            ypos 330
            xsize 980
            ysize 16
            value StaticValue(cola.progreso_tiempo(), 1.0)
            left_bar Solid("#e86a7e" if cola.progreso_tiempo() < 0.35 else "#a7a5f2")
            right_bar Solid("#3a3350")
        if cola.atendidas % 2 == 0:
            fixed at tarjeta_comentario:
                use moderador_tarjeta(cola, creadas)
        else:
            fixed at tarjeta_comentario:
                use moderador_tarjeta(cola, creadas)

        hbox:
            xalign 0.5
            ypos 820
            spacing 60
            textbutton "<  BORRAR":
                xsize 400
                ysize 90
                background Frame("gui/telefono_boton.png", 30, 30)
                hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                text_size 30
                text_bold True
                text_color "#fbf6ee"
                text_xalign 0.5
                text_yalign 0.5
                hover_sound "assets/audio/sfx/menu_hover.ogg"
                action Function(moderar, cola, True)
            textbutton "APROBAR  >":
                xsize 400
                ysize 90
                background Frame("gui/telefono_boton.png", 30, 30)
                hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                text_size 30
                text_bold True
                text_color "#fbf6ee"
                text_xalign 0.5
                text_yalign 0.5
                hover_sound "assets/audio/sfx/menu_hover.ogg"
                action Function(moderar, cola, False)

    if cola.intro > 0:
        add Solid("#000000a0")
        vbox:
            align (0.5, 0.45)
            spacing 20
            text "Los comentarios de Martina están llenos de bots." size 36 color "#fbf6ee" xalign 0.5
            text "Borrar: flecha izquierda, tecla A o cruceta izquierda     Aprobar: flecha derecha, tecla D o cruceta derecha" size 26 bold True color "#facc15" xalign 0.5
            text "Ojo: criticar al alcalde no es desinformación." size 28 color "#c9b8d8" xalign 0.5
            text "%d" % (int(cola.intro) + 1) size 140 bold True color "#ffffff" xalign 0.5

    if cola.terminado():
        add Solid("#000000b0")
        frame:
            align (0.5, 0.5)
            xsize 900
            background Frame("gui/frame.png", 30, 30)
            padding (50, 40)
            vbox:
                spacing 14
                xfill True
                text ("¡COMENTARIOS LIMPIOS!" if cola.exito() else "LOS BOTS GANARON ESTA VEZ") size 46 bold True color ("#2f9e8f" if cola.exito() else "#c0392b") xalign 0.5
                text "Aciertos: [cola.aciertos]   Errores: [cola.errores]   Mejor racha: x[cola.mejor_racha]" size 24 color "#2b2440" xalign 0.5
                text "Puntos: " + formato_num(cola.puntos) size 30 bold True color "#8c2f4b" xalign 0.5
                textbutton "CONTINUAR":
                    style "boton_vn"
                    text_style "boton_vn_text"
                    xalign 0.5
                    default_focus True
                    action Return()
        key "civ_accion" action Return()


label minijuego_moderador(semilla=None, aplicar=True, cantidad=16):
    $ semilla_moderacion = semilla if semilla is not None else renpy.random.randint(1, 999999)
    $ comentarios_mod, creadas_mod = publicaciones_moderacion(semilla_moderacion, cantidad)
    $ moderacion = ColaModeracion(comentarios_mod)
    $ hud_estaba_visible = renpy.get_screen("hud_ciudad") is not None
    $ ocultar_avisos_juego()
    hide screen hud_ciudad
    window hide
    $ renpy.block_rollback()
    call screen moderador_ui(moderacion, creadas_mod)
    hide screen moderador_feedback
    if hud_estaba_visible:
        show screen hud_ciudad
    $ resultado_minijuego = registrar_minijuego(moderacion.resultado(), aplicar)
    $ renpy.block_rollback()
    return resultado_minijuego
