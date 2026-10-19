## Conexion del grafo y los minijuegos con el flujo principal.
## Cada minijuego retorna un dict de resultado; registrar_minijuego() lo
## guarda y aplica sus consecuencias con aplicar_consecuencia() (objects.rpy),
## sin un sistema de estadisticas paralelo.

# Si es False, las publicaciones solo muestran la propagacion BFS y no
# lanzan minijuegos (util cuando la narrativa los llame por su cuenta).
default minijuegos_en_publicaciones = False

# Ultimo resultado de cada minijuego: {"rastreador": {...}, "contencion": {...}, ...}
default registro_minijuegos = {}

init python:

    def registrar_minijuego(resultado, aplicar=True):
        store.registro_minijuegos[resultado["minijuego"]] = resultado
        if aplicar:
            aplicar_consecuencia(resultado["consecuencia"])
            efectos_narrativos(resultado)
        return resultado

    def mostrar_alcance(pub, falsa):
        """Notificacion no bloqueante: el alcance se calcula con BFS desde el jugador."""
        niveles = store.red_civitas.bfs_propagacion(
            "jugador", semilla=pub.nivel_riesgo, factor=store.jugador.get_amplificador() * 1.5)
        alcanzados = [n for nivel in niveles[1:] for n in nivel]
        reposts = sum(store.red_civitas.alcance(n) for n in alcanzados) * REPOSTS_POR_ALCANCE
        renpy.show_screen("alcance_publicacion", cuentas=len(alcanzados), reposts=reposts,
                          minutos=max(1, len(niveles) - 1) * 4, falsa=falsa)

    def accion_elegida(sesion):
        """Que rama del arbol de decisiones termino eligiendo el jugador (ver armar_publicacion)."""
        raiz = sesion.publicacion.arbol.raiz
        verificar = raiz.hijos[1]
        if sesion.actual is raiz.hijos[0]:
            return "compartir"
        if sesion.actual is raiz.hijos[2]:
            return "ignorar"
        if sesion.actual is verificar.hijos[0]:
            return "verificar_si"
        if sesion.actual is verificar.hijos[1]:
            return "verificar_no"
        return None


label reaccion_red_civitas(sesion):
    $ accion_red = accion_elegida(sesion)
    $ pub_red = sesion.publicacion

    if accion_red == "compartir" or accion_red == "verificar_si":
        $ mostrar_alcance(pub_red, accion_red == "compartir" and pub_red.es_falsa)

    if not minijuegos_en_publicaciones:
        return

    if accion_red == "compartir" and pub_red.es_falsa and pub_red.nivel_riesgo >= 55:
        if pub_red.nivel_riesgo >= 85 and "viralizacion" not in registro_minijuegos:
            "Tu repost encendio la mecha. La publicacion se esta volviendo viral en Civitas."
            call evento_gran_viralizacion
        elif "contencion" not in registro_minijuegos:
            "La publicacion falsa que compartiste se expande sin control. Hay que contenerla."
            call minijuego_contencion

    elif accion_red == "verificar_no" and pub_red.es_falsa and pub_red.nivel_riesgo >= 75 and "rastreador" not in registro_minijuegos:
        "Reportaste la publicacion. Aun puedes rastrear quien la origino."
        menu:
            "Rastrear el origen":
                call minijuego_rastreador
            "Dejarlo asi":
                pass

    return


transform notificacion_entrada:
    on show:
        alpha 0.0 yoffset -80
        easein 0.35 alpha 1.0 yoffset 0
    on hide:
        easeout 0.35 alpha 0.0 yoffset -80


screen alcance_publicacion(cuentas, reposts, minutos, falsa):
    zorder 60
    frame at notificacion_entrada:
        xalign 0.5
        ypos 24
        xsize 520
        background ("#7f1d1df0" if falsa else "#14532df0")
        padding (24, 16)
        vbox:
            spacing 4
            text "CIVITAS" size 16 bold True color "#fde68a"
            text ("Tu repost de la noticia falsa se esta moviendo" if falsa else "Tu publicacion esta circulando") size 22 bold True color "#ffffff"
            text "Llego a %d cuentas  -  %s reposts en %d min" % (cuentas, formato_num(reposts), minutos) size 19 color "#f1f5f9"
    timer 4.5 action Hide("alcance_publicacion")
