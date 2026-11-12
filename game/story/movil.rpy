## Telefonos (variante "small"): el juego se diseño a 1920x1080 y en una pantalla de 6" el texto de
## las pantallas propias queda diminuto. La primera vez se sube el escalado de texto de Ren'Py;
## el jugador puede cambiarlo despues en Opciones > Accesibilidad (Shift+A).

default persistent.escala_movil_aplicada = False

init 1 python:
    if renpy.variant("small") and not persistent.escala_movil_aplicada:
        _preferences.font_size = 1.2
        persistent.escala_movil_aplicada = True
