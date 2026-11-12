init python:
    from clases.Publicacion import SesionPublicacion, BancoPublicaciones, armar_publicacion
    from clases.publicaciones_historia import PUBLICACIONES_HISTORIA
    from clases.Ciudad import Ciudad
    from clases.Jugador import Jugador

    def aplicar_consecuencia(consecuencia):
        if not consecuencia:
            return
        for clave, valor in consecuencia.items():
            if clave == 'puntos':
                if valor > 0:
                    store.jugador.ganar_puntos(valor)
                else:
                    store.jugador.perder_puntos(-valor)
            elif clave == 'reputacion':
                store.jugador.reputacion = max(0, min(100, store.jugador.reputacion + valor))
            elif hasattr(store.ciudad, clave):
                nuevo = max(0, min(100, getattr(store.ciudad, clave) + valor))
                setattr(store.ciudad, clave, nuevo)
        mostrar_cambios(consecuencia)

label nueva_publicacion:
    if not banco.hay_mas():
        return

    $ sesion = SesionPublicacion(banco.siguiente())
    $ publicaciones_vistas += 1
    play sound "assets/audio/sfx/notificacion.wav"
    window hide

    while not sesion.terminada():
        $ eleccion = renpy.call_screen("telefono_civitas", sesion=sesion)
        $ sesion.elegir(eleccion)

    window auto
    civitas "[sesion.actual.texto]"

    $ aplicar_consecuencia(sesion.actual.consecuencia)
    $ ultima_accion = accion_elegida(sesion)
    $ ultima_publicacion_falsa = sesion.publicacion.es_falsa
    $ registrar_decision_publicacion(sesion.publicacion, ultima_accion)

    call reaccion_red_civitas(sesion)

    $ razon_derrota = ciudad.derrota_inmediata() or ""
    if razon_derrota:
        jump final_caos

    return

default publicaciones_vistas = 0
default ultima_accion = None
default ultima_publicacion_falsa = False

# Estado de la ciudad y del jugador

default ciudad = Ciudad()
default jugador = Jugador("Alcalde")
default razon_derrota = ""

# Banco de publicaciones — insertadas en AVL por nivel_riesgo, entregadas de menor a mayor
# Cada publicacion tiene 4 acciones segun el diagrama del PDF (pag. 4):
#   Compartir | Verificar (Si/No) | Ignorar

default banco = BancoPublicaciones([armar_publicacion(**p) for p in PUBLICACIONES_HISTORIA])
