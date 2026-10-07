define HUD_X0 = 105
define HUD_ANCHO = 230
define HUD_Y = 18

screen hud_ciudad():
    zorder 50
    frame:
        xalign 0.5 yalign 0.0
        padding (20, 10)
        background "#0f172acc"
        hbox:
            spacing 0
            for clave, etiqueta, positivo in INDICADORES_HUD:
                use celda_indicador(clave, etiqueta, positivo)
            null width 30
            vbox:
                xsize 160
                text "Reputación" size 18 color "#fbbf24"
                text "[jugador.get_reputacion()]" size 28 color "#fbbf24"
            vbox:
                xsize 140
                text "Puntos" size 18 color "#fbbf24"
                text "[jugador.get_puntos()]" size 28 color "#fbbf24"

screen celda_indicador(clave, etiqueta, positivo):
    $ val = valor_indicador(clave)
    $ crit = es_critico(clave)
    $ col = ("#4ade80" if positivo else "#f87171") if not crit else "#ff5252"
    fixed:
        xsize HUD_ANCHO ysize 70
        at (celda_tiembla if (crit and efectos_activos()) else celda_quieta)
        vbox:
            spacing 2
            text etiqueta size 18 color "#cbd5e1"
            text "[val]" size 28 color col
            bar:
                value StaticValue(val, 100)
                xsize HUD_ANCHO - 30 ysize 6
                left_bar Solid(col)
                right_bar Solid("#334155")
