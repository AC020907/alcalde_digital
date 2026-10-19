## Evento "La Gran Viralizacion" (arcade, version extrema de Caza-Rumores).
## Uso:  call evento_gran_viralizacion
## El rumor arranca con varias oleadas ya calculadas por BFS, viaja mas
## rapido y aparecen focos nuevos mas seguido.

label evento_gran_viralizacion(origen=None, semilla=None, aplicar=True, ajustes=None):
    $ semilla_viral = semilla if semilla is not None else renpy.random.randint(1, 999999)
    $ focos_viral = focos_viralizacion(red_civitas, origen or ORIGEN_RUMOR, semilla_viral, 2)
    $ viralizacion = CazaRumores(red_civitas, "viral", focos_viral, semilla_viral, ajustes)
    call jugar_arcade(viralizacion, "LA GRAN VIRALIZACION", RUMORES[semilla_viral % len(RUMORES)])
    $ resultado_minijuego = registrar_minijuego(viralizacion.resultado(), aplicar)
    return resultado_minijuego
