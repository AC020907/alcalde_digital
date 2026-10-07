default persistent.efectos_reducidos = False
default flot_n = 0            # contador para tags únicos de flotantes

init python:
    RIESGO_SHAKE = 75

    # clave -> (etiqueta, positivo, umbral crítico, comparador)
    INDICADORES_HUD = [
        ("info_verificada", "Info verificada", True),
        ("confianza",       "Confianza",       True),
        ("convivencia",     "Convivencia",     True),
        ("bienestar",       "Bienestar",       True),
        ("desinformacion",  "Desinformación",  False),
        ("conflictos",      "Conflictos",      False),
    ]
    UMBRAL_CRITICO = {            # (comparador, valor)
        "info_verificada": ("<=", 25),
        "confianza":       ("<=", 35),   # derrota real en <= 20
        "convivencia":     ("<=", 30),
        "bienestar":       ("<=", 30),
        "desinformacion":  (">=", 65),   # derrota real en >= 80
        "conflictos":      (">=", 65),   # derrota real en >= 80
    }

    def valor_indicador(clave):
        if clave in ("reputacion", "puntos"):
            return getattr(store.jugador, clave)
        return getattr(store.ciudad, clave)

    def es_critico(clave):
        if clave not in UMBRAL_CRITICO:
            return False
        op, lim = UMBRAL_CRITICO[clave]
        v = valor_indicador(clave)
        return v <= lim if op == "<=" else v >= lim

    def efectos_activos():
        return not persistent.efectos_reducidos

    def estado_ciudad():
        c = store.ciudad
        if c.desinformacion >= 65 or c.conflictos >= 65 or c.confianza <= 35:
            return "critico"
        if c.desinformacion >= 45 or c.conflictos >= 40 or c.confianza <= 50:
            return "tenso"
        if c.info_verificada >= 70 and c.desinformacion <= 30 and c.confianza >= 65:
            return "informado"
        return "normal"

    def indice_hud(clave):
        for i, (c, _e, _p) in enumerate(INDICADORES_HUD):
            if c == clave:
                return i
        return None

    def datos_flotante(clave, delta):
        i = indice_hud(clave)
        if i is None:
            if clave == "reputacion":
                x = 105 + 6 * 230 + 30 + 80
            else:
                x = 105 + 6 * 230 + 30 + 160 + 70
            positivo = True
        else:
            x = 105 + i * 230 + 230 // 2
            positivo = INDICADORES_HUD[i][2]
        mejora = (delta > 0) == positivo
        color = "#4ade80" if mejora else "#f87171"
        signo = "+%d" % delta if delta > 0 else "%d" % delta
        return x, 18 + 80, signo, color

    def notificar_cambio(clave, delta):
        if delta == 0 or renpy.get_screen("hud_ciudad") is None:
            return
        store.flot_n += 1
        retraso = 0.12 * (store.flot_n % 4)
        tag = "flot_%d" % store.flot_n
        renpy.show_screen("flotante", clave, delta, retraso, tag, _tag=tag)

    def sacudir(intensidad=1.0):
        if persistent.efectos_reducidos:
            return
        renpy.show_layer_at(sacudida, layer="master", reset=True)
        renpy.show_layer_at(sacudida, layer="screens", reset=True)
        renpy.sound.play("assets/audio/sfx/impacto.wav")

transform tarjeta_entra:
    on show:
        xoffset 700 alpha 0.0
        easein_back 0.5 xoffset 0 alpha 1.0
    on hide:
        easeout 0.3 xoffset 700 alpha 0.0

transform tarjeta_fade:
    on show:
        alpha 0.0
        linear 0.3 alpha 1.0
    on hide:
        linear 0.3 alpha 0.0

transform sacudida:
    block:
        ease 0.04 xoffset 16  yoffset -9
        ease 0.04 xoffset -14 yoffset 7
        ease 0.04 xoffset 11  yoffset -6
        ease 0.04 xoffset -9  yoffset 5
        ease 0.04 xoffset 5   yoffset -3
        repeat 2
    ease 0.06 xoffset 0 yoffset 0

transform celda_quieta:
    pass

transform celda_tiembla:
    block:
        linear 0.05 xoffset 3
        linear 0.05 xoffset -3
        linear 0.05 xoffset 2
        linear 0.05 xoffset -2
        pause 0.35
        repeat

transform flotar(retraso=0.0, dur=1.5):
    alpha 0.0 yoffset 0
    pause retraso
    parallel:
        linear 0.15 alpha 1.0
        pause (dur - 0.45)
        linear 0.30 alpha 0.0
    parallel:
        easeout_cubic dur yoffset -70

transform flotar_estatico(retraso=0.0, dur=1.5):
    alpha 0.0
    pause retraso
    linear 0.15 alpha 1.0
    pause (dur - 0.45)
    linear 0.30 alpha 0.0

screen flotante(clave, delta, retraso, tag):
    zorder 60
    $ x, y, texto, color = datos_flotante(clave, delta)
    text texto:
        xpos x xanchor 0.5 ypos y
        size 40 bold True color color
        outlines [(3, "#000000", 0, 0)]
        at (flotar(retraso) if efectos_activos() else flotar_estatico(retraso))
    timer 1.5 + retraso + 0.2 action Function(renpy.hide_screen, tag)
