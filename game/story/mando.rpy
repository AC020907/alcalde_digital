## Mando: acciones comunes para teclado y gamepad. Las pantallas y los displayables preguntan por
## estas acciones (key "civ_..." o renpy.map_event) en vez de por teclas concretas.
##
##   Cruceta / palanca izq.   moverse, conducir, mover la mira
##   A                        aceptar, avanzar, seleccionar ficha o hueco, disparar
##   B                        menu del juego / cerrar
##   X                        onda (Caza-Rumores) · aprobar comentario no
##   Y                        pista
##   LB                       volver un paso (rastreo)
##   Start                    pausa

init python:

    CIV_TECLADO = {
        "civ_izq": ["K_LEFT", "K_a"], "civ_der": ["K_RIGHT", "K_d"],
        "civ_arriba": ["K_UP", "K_w"], "civ_abajo": ["K_DOWN", "K_s"],
        "civ_izq_fin": ["keyup_K_LEFT", "keyup_K_a"], "civ_der_fin": ["keyup_K_RIGHT", "keyup_K_d"],
        "civ_arriba_fin": ["keyup_K_UP", "keyup_K_w"], "civ_abajo_fin": ["keyup_K_DOWN", "keyup_K_s"],
        "civ_accion": ["K_RETURN", "K_KP_ENTER", "K_SPACE"],
        "civ_onda": ["K_SPACE"],
        "civ_pista": ["K_h"],
        "civ_volver": ["K_BACKSPACE"],
    }
    config.keymap.update(CIV_TECLADO)

    def _vincular_pad(evento, *acciones):
        config.pad_bindings[evento] = list(config.pad_bindings.get(evento, [])) + list(acciones)

    # A tambien "agarra y suelta" en el mismo evento: un drag sin movimiento ejecuta su clicked,
    # asi las fichas del Rastreador se eligen y colocan sin arrastrar.
    _vincular_pad("pad_a_press", "drag_activate", "drag_deactivate", "civ_accion")
    _vincular_pad("pad_x_press", "civ_onda")
    # Y por defecto oculta la interfaz (abre un contexto modal que congela los minijuegos): aqui es "pista".
    config.pad_bindings["pad_y_press"] = ["civ_pista"]
    _vincular_pad("pad_leftshoulder_press", "civ_volver")

    for _dir, _cruceta, _eje in (("izq", "dpleft", "leftx_neg"), ("der", "dpright", "leftx_pos"),
                                 ("arriba", "dpup", "lefty_neg"), ("abajo", "dpdown", "lefty_pos")):
        _vincular_pad("pad_%s_press" % _cruceta, "civ_" + _dir)
        _vincular_pad("pad_%s_release" % _cruceta, "civ_%s_fin" % _dir)
        _vincular_pad("pad_" + _eje, "civ_" + _dir)
    _vincular_pad("pad_leftx_zero", "civ_izq_fin", "civ_der_fin")
    _vincular_pad("pad_lefty_zero", "civ_arriba_fin", "civ_abajo_fin")

    DIRECCIONES_CIV = (("civ_izq", "civ_izq_fin", (-1, 0)), ("civ_der", "civ_der_fin", (1, 0)),
                       ("civ_arriba", "civ_arriba_fin", (0, -1)), ("civ_abajo", "civ_abajo_fin", (0, 1)))

    def direccion_evento(ev):
        """(nombre, vector, pulsada) si el evento es una direccion de teclado o mando; si no, None."""
        for inicio, fin, vector in DIRECCIONES_CIV:
            if renpy.map_event(ev, inicio):
                return inicio, vector, True
            if renpy.map_event(ev, fin):
                return inicio, vector, False
        return None


## Ayuda de controles para la pantalla de opciones.
screen ayuda_mando():
    vbox:
        spacing 4
        label _("Mando")
        for fila in (_("Cruceta / palanca: moverse y elegir"), _("A: aceptar · B: menú / cerrar"),
                     _("X: onda · Y: pista · LB: volver un paso"), _("Start: pausa")):
            text fila size 20 color "#5b4f72"
