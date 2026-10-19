## Minijuego 2 - Moderador (tiempo real).
## Uso:  call minijuego_moderador             (semilla aleatoria)
##       call minijuego_moderador(semilla=7)  (partida reproducible)

init python:
    from clases.Moderador import ColaModeracion
    from clases.Publicacion import Publicacion

    # (autor, texto, creada, es_bot). Ojo: la critica dura pero real NO se borra.
    COMENTARIOS_MODERACION = [
        ("@noticias_YA_2391", "COMPARTE ANTES DE QUE LO BORREN!!! la alcaldia esconde la verdad bit.ly/v3rd4d", "hace 2 dias", True),
        ("@lucia.marquez", "Martina, ¿tienes la fuente de lo del agua? Mi mamá está preocupada.", "2017", False),
        ("@verdad.oculta.77", "EL AGUA ESTA ENVENENADA. NO LA TOMEN. LOS MEDIOS CALLAN.", "ayer", True),
        ("@don.pedro", "Yo vivo en el Barrio Sur y el agua sale normal, no exageren.", "2022", False),
        ("@patriota_nova_01", "Despierten!!! #CiudadNovaMiente #CiudadNovaMiente #CiudadNovaMiente", "hace 3 dias", True),
        ("@camila.r", "El alcalde llega tarde a todo. Igual que con los huecos de mi calle.", "2019", False),
        ("@info24_real", "Gana un bono de 500.000 si compartes esto con 10 amigos", "hace 1 dia", True),
        ("@profe.andres", "Antes de compartir, revisen el comunicado oficial de la empresa de acueducto.", "2015", False),
        ("@user8812345", "yo tambien lo vi yo tambien lo vi yo tambien lo vi", "hoy", True),
        ("@sofia.sur", "No me gusta la gestión del alcalde, pero esto del agua suena a mentira.", "2018", False),
        ("@alerta_ciudadana_x", "URGENTE: mañana cortan el agua en toda la ciudad (fuente: confía)", "hace 4 dias", True),
        ("@marta.ventas", "Martina, te sigo hace años y te pido que verifiques antes de publicar.", "2015", False),
        ("@bot_nova_445", "Los que defienden al alcalde están pagados. Todos.", "ayer", True),
        ("@leo.centro", "Qué pereza este tema, mejor hablemos de los conciertos del sábado jaja", "2019", False),
        ("@nova.libre.real", "Video filtrado: funcionarios echando químicos al tanque >> bit.ly/xx9", "hace 2 dias", True),
        ("@pipe.skate", "Esta administración es un desastre y lo voy a seguir diciendo.", "2023", False),
        ("@ciudadano_consciente_9", "Si no compartes eres cómplice. #DespiertaNova", "hoy", True),
        ("@lector.critico", "La universidad publicó análisis del agua de ayer: todo dentro de lo normal.", "2016", False),
        ("@hidro_verdad", "Mi primo trabaja en el acueducto y dice que es cierto (no puede dar su nombre)", "hace 6 dias", True),
        ("@fan.noticias", "Martina, ¿vas a hacer live hoy? Quiero preguntarte sobre esto.", "2020", False),
        ("@xx_ciudadnova_xx", "RT RT RT RT el agua el agua el agua", "hoy", True),
        ("@vecino.anonimo", "Soy nuevo en Civitas y no sé a quién creerle, la verdad.", "2024", False),
    ]

    def publicaciones_moderacion(semilla, cantidad=16):
        rng = random.Random("moderacion|%s" % semilla)
        elegidos = rng.sample(COMENTARIOS_MODERACION, cantidad)
        return [Publicacion(autor, texto, es_bot, 0, None) for autor, texto, _, es_bot in elegidos], \
               {autor: creada for autor, _, creada, _ in elegidos}

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
        timer 0.05 repeat True action Function(tick_moderacion, cola, 0.05)
        if cola.jugando():
            key "K_LEFT" action Function(moderar, cola, True)
            key "K_a" action Function(moderar, cola, True)
            key "K_RIGHT" action Function(moderar, cola, False)
            key "K_d" action Function(moderar, cola, False)

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

    if cola.actual is not None and cola.intro <= 0:
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
            textbutton "<  BORRAR  (A)":
                xsize 400
                ysize 90
                background Frame("gui/telefono_boton.png", 30, 30)
                hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                text_size 30
                text_bold True
                text_color "#fbf6ee"
                text_xalign 0.5
                text_yalign 0.5
                hover_sound "assets/audio/sfx/ui_hover.wav"
                action Function(moderar, cola, True)
            textbutton "APROBAR  (D)  >":
                xsize 400
                ysize 90
                background Frame("gui/telefono_boton.png", 30, 30)
                hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                text_size 30
                text_bold True
                text_color "#fbf6ee"
                text_xalign 0.5
                text_yalign 0.5
                hover_sound "assets/audio/sfx/ui_hover.wav"
                action Function(moderar, cola, False)

    if cola.intro > 0:
        add Solid("#000000a0")
        vbox:
            align (0.5, 0.45)
            spacing 20
            text "Los comentarios de Martina están llenos de bots." size 36 color "#fbf6ee" xalign 0.5
            text "← o A: borrar     → o D: aprobar" size 32 bold True color "#facc15" xalign 0.5
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
                    style "grafo_button"
                    text_style "grafo_button_text"
                    xalign 0.5
                    xsize 360
                    text_xalign 0.5
                    action Return()


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
