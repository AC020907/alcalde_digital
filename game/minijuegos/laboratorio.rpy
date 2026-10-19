## Laboratorio de minijuegos (solo desarrollo).
## Abrir desde el menu principal con Shift+L (solo con config.developer,
## es decir, al lanzar desde el Ren'Py Launcher). No afecta el juego normal.

init python:

    def abrir_laboratorio_grafos():
        if config.developer and main_menu:
            renpy.run(Start("laboratorio_grafos"))

    config.keymap["laboratorio_grafos"] = ["shift_K_l"]
    config.underlay.append(renpy.Keymap(laboratorio_grafos=abrir_laboratorio_grafos))


label laboratorio_grafos:
    scene black
    show screen hud_ciudad
    $ estado_sustentacion = "ACTIVADO" if modo_sustentacion else "apagado"
    $ _return = None

    menu:
        "Laboratorio - modo sustentacion: [estado_sustentacion]"

        "Minijuego 1 - Rastreador (tablero de evidencias)":
            call minijuego_rastreador

        "Minijuego 1 - Rastreador corto (feria)":
            call minijuego_rastreador(ajustes=FERIA_RASTREO)

        "Minijuego 1b - Rastreador en vivo (arcade)":
            call minijuego_rastreador_vivo

        "Minijuego 3 - Contencion viral":
            call minijuego_contencion

        "Evento - La Gran Viralizacion":
            call evento_gran_viralizacion

        "Minijuego 2 - Moderador (estructura)":
            call minijuego_moderador

        "QA - Revisión visual de sprites, encuadres y fondos":
            call revision_visual

        "QA - CivitasNet con todas las publicaciones":
            $ memoria["momento"] = inv.DOMINGO
            call abrir_civitasnet

        "QA - Expediente con todas las fichas":
            python:
                for _pid in inv.PISTAS:
                    dar_pista(_pid, aviso=False)
            $ renpy.show_screen("expediente")
            "Revisa las fichas y cierra el expediente con Esc."

        "QA - Eventos de esta semilla: [memoria[semilla]] -> [memoria[eventos]]":
            $ preparar_partida()

        "Activar / desactivar modo sustentacion (boton RED INTERNA)":
            $ modo_sustentacion = not modo_sustentacion

        "Sustentacion: demostracion de propagacion BFS":
            call animar_propagacion(titulo="Demostracion BFS desde el jugador")

        "Sustentacion: BFS probabilistico (semilla aleatoria)":
            $ semilla_lab = renpy.random.randint(1, 9999)
            call animar_propagacion(titulo="BFS probabilistico - semilla %d" % semilla_lab, semilla=semilla_lab, factor=1.5)

        "Salir al menu principal":
            hide screen hud_ciudad
            return

    if _return and isinstance(_return, dict):
        $ texto_resultado = _return["mensaje"]
        "Resultado: [texto_resultado]"

    jump laboratorio_grafos
