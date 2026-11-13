# Overlay de color de la ciudad.
# Una pantalla por estado (tag "ov_<estado>"): al cambiar de estado se oculta la
# anterior (on hide: se desvanece) y se muestra la nueva (on show: aparece), lo que
# produce el fundido cruzado. La actualizacion se dispara desde aplicar_consecuencia
# (actualizar_overlay) y no depende de que Ren'Py re-evalue la pantalla.

default ov_actual = None

define COLOR_ESTADO = {
    "normal":    ("#3b82f6", 0.07),   # azul tranquilo
    "tenso":     ("#fb923c", 0.16),   # naranja
    "informado": ("#22c55e", 0.10),   # verde
    "critico":   ("#dc2626", 0.22),   # rojo
}

transform capa_tinte(a):
    on show:
        alpha 0.0
        linear 1.2 alpha a
    on hide:
        linear 1.2 alpha 0.0

transform pulso_vignette:
    alpha 0.35
    linear 0.9 alpha 0.85
    linear 0.9 alpha 0.35
    repeat

screen overlay_estado(est):
    zorder -5
    $ color, alfa = COLOR_ESTADO[est]
    add Solid(color) at capa_tinte(alfa)
    if est == "critico" and efectos_activos():
        add "assets/ui/vignette_roja.png" at pulso_vignette

init python:
    def actualizar_overlay(forzar=False):
        """Muestra el overlay del estado actual de la ciudad (fundido cruzado si cambia)."""
        est = estado_ciudad()
        if est == store.ov_actual and not forzar:
            return
        if store.ov_actual:
            renpy.hide_screen("ov_" + store.ov_actual)
        renpy.show_screen("overlay_estado", est, _tag="ov_" + est)
        store.ov_actual = est

    def ocultar_overlay():
        for est in COLOR_ESTADO:
            renpy.hide_screen("ov_" + est)
        store.ov_actual = None
