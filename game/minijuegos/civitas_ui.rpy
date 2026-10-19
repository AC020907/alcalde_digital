## Utilidades compartidas de presentacion: sonidos, formato de numeros y avatares.

init python:
    import random
    from clases.ConfigMinijuegos import REPOSTS_POR_ALCANCE
    from clases.RedCivitas import CANDIDATOS_FOCO, RUMORES

    # Hooks de audio para Dev 4: suenan solo si el archivo existe.
    SONIDO_AVISO = {
        "bueno":  "assets/audio/sfx/nodo_contenido.wav",
        "malo":   "assets/audio/sfx/nodo_infectado.wav",
        "alerta": "assets/audio/sfx/alarma_viral.wav",
        "info":   "assets/audio/sfx/rastreo_paso.wav",
    }
    SONIDO_EXITO = "assets/audio/sfx/exito.wav"
    SONIDO_FALLO = "assets/audio/sfx/fallo.wav"

    def sonar(ruta):
        if ruta and renpy.loadable(ruta):
            renpy.sound.play(ruta)

    def ocultar_avisos_juego():
        for pantalla in ("alcance_publicacion", "cambios_indicadores", "notify", "tarjeta_lugar",
                         "moderador_feedback", "puzzle_feedback"):
            renpy.hide_screen(pantalla)

    def formato_num(n):
        return "{:,}".format(int(n)).replace(",", ".")

    def icono_aparente(grafo, nodo, revelar_bot):
        """Los bots parecen ciudadanos hasta que el jugador los descubre."""
        tipo = grafo.tipo(nodo)
        if tipo == "bot" and not revelar_bot:
            tipo = "ciudadano"
        return ICONO_TIPO[tipo]
