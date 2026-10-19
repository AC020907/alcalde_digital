## Minijuego 3 - Contencion: "Caza-Rumores" (arcade).
## Uso:  call minijuego_contencion             (semilla aleatoria)
##       call minijuego_contencion(semilla=7)  (partida reproducible)
## Retorna (en _return) el dict de CazaRumores.resultado().

label minijuego_contencion(focos=None, semilla=None, aplicar=True, ajustes=None):
    $ semilla_contencion = semilla if semilla is not None else renpy.random.randint(1, 999999)
    $ focos_contencion = focos or random.Random("focos|%s" % semilla_contencion).sample(CANDIDATOS_FOCO, 2)
    $ contencion = CazaRumores(red_civitas, "contencion", focos_contencion, semilla_contencion, ajustes)
    call jugar_arcade(contencion, "CAZA-RUMORES", RUMORES[semilla_contencion % len(RUMORES)])
    $ resultado_minijuego = registrar_minijuego(contencion.resultado(), aplicar)
    return resultado_minijuego
