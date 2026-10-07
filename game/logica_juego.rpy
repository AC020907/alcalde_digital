init python:
    from clases.Publicacion import SesionPublicacion, BancoPublicaciones, armar_publicacion
    from clases.Ciudad import Ciudad
    from clases.Jugador import Jugador

    def aplicar_consecuencia(consecuencia):
        if not consecuencia:
            return
        amp = store.jugador.get_amplificador()
        for clave, valor in consecuencia.items():
            if clave == 'puntos':
                antes = store.jugador.puntos
                if valor > 0:
                    store.jugador.ganar_puntos(valor)      # ya amplifica internamente
                else:
                    store.jugador.perder_puntos(-valor)    # ya amplifica internamente
                _cambio(clave, store.jugador.puntos - antes)
            elif clave == 'reputacion':
                antes = store.jugador.reputacion
                store.jugador.reputacion = max(0, min(100, antes + int(round(valor * amp))))
                _cambio(clave, store.jugador.reputacion - antes)
            elif hasattr(store.ciudad, clave):
                antes = getattr(store.ciudad, clave)
                nuevo = max(0, min(100, antes + int(round(valor * amp))))
                setattr(store.ciudad, clave, nuevo)
                _cambio(clave, nuevo - antes)
        actualizar_overlay()
        renpy.restart_interaction()

    def _cambio(clave, delta):
        notificar_cambio(clave, delta)

label nueva_publicacion:
    if not banco.hay_mas():
        return

    $ sesion = SesionPublicacion(banco.siguiente())
    $ tarj_likes = renpy.random.randint(8, 60) * (1 + sesion.publicacion.nivel_riesgo // 25)
    $ tarj_reposts = renpy.random.randint(2, 20) * (1 + sesion.publicacion.nivel_riesgo // 25)
    $ tarj_avatar = "images/placeholder%d.png" % (sum(ord(c) for c in sesion.publicacion.autor) % 3 + 1)
    show screen civitas_tarjeta(sesion.publicacion.autor, sesion.publicacion.contenido, tarj_likes, tarj_reposts, tarj_avatar)
    if sesion.publicacion.nivel_riesgo >= RIESGO_SHAKE:
        $ sacudir()
    "[sesion.actual.texto]"

    while not sesion.terminada():
        if sesion.en_verificacion():
            $ veredicto = "FALSA" if sesion.publicacion.es_falsa else "VERDADERA"
            "Contrastas con fuentes oficiales... La publicación es [veredicto]."
            $ sesion.resolver_verificacion()
        else:
            $ eleccion = renpy.display_menu(sesion.opciones())
            $ sesion.elegir(eleccion)
        if sesion.terminada():
            $ aplicar_consecuencia(sesion.actual.consecuencia)
        "[sesion.actual.texto]"

    hide screen civitas_tarjeta

    $ razon_derrota = ciudad.derrota_inmediata() or ""
    if razon_derrota:
        jump derrota
    return
