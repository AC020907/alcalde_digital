## Telefono de Civitas: asi recibe y responde el jugador cada publicacion del banco (AVL).
## La decision recorre el arbol N-ario de la publicacion (SesionPublicacion).

init python:

    def avatar_autor(autor):
        if red_civitas.existe(autor):
            return icono_aparente(red_civitas, autor, False)
        return ICONO_TIPO["ciudadano"]

    def estilo_opcion(etiqueta):
        e = etiqueta.lower()
        if e.startswith("compartir"):
            return "#e86a7e"
        if e.startswith("ignorar"):
            return "#8b84a8"
        if "falsa" in e or "falso" in e or "reportar" in e or "propaganda" in e or "exagerado" in e or "fabricado" in e:
            return "#f59e0b"
        return "#7dd3fc"


transform telefono_entrada:
    on show:
        alpha 0.0 yoffset 120
        easein 0.4 alpha 1.0 yoffset 0
    on hide:
        easeout 0.25 alpha 0.0 yoffset 60

transform opcion_telefono(retraso):
    alpha 0.0 xoffset 40
    pause retraso
    easein 0.25 alpha 1.0 xoffset 0
    on hover:
        easein 0.1 zoom 1.03
    on idle:
        easein 0.1 zoom 1.0

screen telefono_civitas(sesion):
    modal True
    zorder 45
    default progreso = 0.0
    $ pub = sesion.publicacion
    $ reposts = int(pub.nivel_riesgo * 137 * progreso)
    $ me_gusta = int(pub.nivel_riesgo * 61 * progreso)

    timer 0.04 repeat True action SetScreenVariable("progreso", min(1.0, progreso + 0.04))
    add Solid("#1b142699")

    fixed at telefono_entrada:
        xysize (600, 960)
        xalign 0.5
        ypos 40
        add "gui/telefono.png"

        vbox:
            xpos 60
            ypos 74
            xsize 480
            spacing 14

            hbox:
                spacing 10
                text "CIVITAS" size 30 bold True color "#a7a5f2" kerning 3
                text "Ciudad Nova" size 16 color "#8b84a8" yalign 0.7
            frame:
                xfill True
                background Frame("gui/telefono_post.png", 24, 24)
                padding (22, 20)
                vbox:
                    spacing 12
                    hbox:
                        spacing 12
                        add Transform(avatar_autor(pub.autor), xysize=(62, 62))
                        vbox:
                            yalign 0.5
                            text pub.autor size 22 bold True color "#fbf6ee"
                            text "hace %d min  -  publicación" % max(2, pub.nivel_riesgo // 6) size 15 color "#8b84a8"
                    text pub.contenido size 23 color "#ece6ff"
                    hbox:
                        spacing 26
                        text "%s reposts" % formato_num(reposts) size 17 bold True color "#e86a7e"
                        text "%s me gusta" % formato_num(me_gusta) size 17 color "#a7a5f2"
                    if pub.nivel_riesgo >= 55:
                        text "TENDENCIA EN TU ZONA" size 14 bold True color "#f59e0b" kerning 2

            null height 4
            text sesion.actual.texto.replace("?Que", "¿Qué").replace("?Es", "¿Es") size 24 bold True color "#fbf6ee"

            for i, (etiqueta, indice) in enumerate(sesion.opciones()):
                button:
                    xfill True
                    ysize 64
                    background Frame("gui/telefono_boton.png", 30, 30)
                    hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                    hover_sound "assets/audio/sfx/ui_hover.wav"
                    activate_sound "assets/audio/sfx/eleccion.wav"
                    action Return(indice)
                    at opcion_telefono(0.2 + i * 0.08)
                    hbox:
                        xpos 22
                        yalign 0.5
                        spacing 12
                        add Solid(estilo_opcion(etiqueta), xysize=(10, 30)) yalign 0.5
                        text etiqueta size 20 color "#fbf6ee" yalign 0.5 xmaximum 400
