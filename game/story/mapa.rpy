## MAPA DE CIUDAD NOVA: el alcalde maneja el carro por las calles hasta cada lugar.
## La logica (grafo de calles, movimiento y rumbo) vive en clases/MapaCiudad.py;
## aqui solo se dibuja el mapa y se traduce el teclado a la direccion del carro.
## La historia usa el mapa para moverse: antes de cada escena llama a
## viajar_a_mision("id") y la escena empieza solo cuando el jugador llega al lugar.
## Fuera de esos viajes el mapa se puede abrir libremente desde el HUD.

default mapa_posicion = None
default ubicacion_actual = None
default mapa_objetivo = None

init python:
    import pygame
    from clases import Misiones as misiones
    from clases.MapaCiudad import (crear_mapa_nova, Carro, RUMBOS, UBICACIONES_FERIA,
                                   ANCHO_REF, ALTO_REF)

    MAPA_NOVA = crear_mapa_nova()
    MAPA_INICIO = "alcaldia"
    MAPA_IMAGEN = "images/bg/mapa.jpg"
    MAPA_ESCALA = 1920.0 / ANCHO_REF          # pixeles de pantalla por pixel de referencia
    MAPA_ZOOM_IMAGEN = 1920.0 / 3072.0
    MAPA_ZOOM_CARRO = 0.34
    MAPA_CAJA_CARRO = (120, 90)
    MAPA_CARPETA_CARRO = "images/personajes/Sprites_carro/Carro_%s/%d.png"
    MAPA_CUADROS_POR_SEGUNDO = 9

    # id -> (nombre, descripcion, centro del rotulo en el mapa de referencia)
    UBICACIONES = {
        "centro": ("Centro", "La plaza donde todo se comenta.", (1000, 413)),
        "alcaldia": ("Alcaldía", "Tu despacho y el centro de operaciones.", (1285, 698)),
        "prensa": ("Prensa", "Las redacciones de Ciudad Nova.", (1370, 240)),
        "barrio_sur": ("Barrio Sur", "Donde los rumores corren más rápido.", (980, 1080)),
        "universidad": ("Universidad", "Aulas, estudiantes y mucho debate.", (775, 180)),
        "barrio_norte": ("Barrio Norte", "Casas, vecinos y grupos de chat.", (360, 410)),
        "parque": ("Parque Central", "El lago y la gente de siempre.", (420, 838)),
        "transporte": ("Transporte Público", "Todos pasan por aquí cada día.", (1580, 994)),
    }

    # Radio (px de referencia) a menos del cual se considera que el carro llego a un lugar.
    MAPA_RADIO_LLEGADA = 70.0

    def mision_actual():
        return misiones.mision_activa(store.misiones_hechas, store.modo_feria_activo)

    def mision_destino():
        """La mision que se esta viajando; si no hay viaje, la siguiente de la historia."""
        if store.mapa_objetivo in misiones.POR_ID:
            return misiones.POR_ID[store.mapa_objetivo]
        return mision_actual()

    def abrir_mapa_libre():
        if renpy.get_screen("mapa_viaje") is None:
            renpy.show_screen("mapa_ciudad")

    def mapa_ya_en(ubicacion):
        carro = Carro(MAPA_NOVA, MAPA_INICIO)
        if store.mapa_posicion:
            carro.restaurar(store.mapa_posicion)
        return carro.ubicacion_cercana(MAPA_RADIO_LLEGADA) == ubicacion

    def mapa_debe_conducir(mision_id):
        """En el Modo Feria solo se conducen algunos viajes; tampoco hace falta si ya se esta en el lugar."""
        if store.modo_feria_activo and mision_id not in misiones.FERIA_CONDUCIR:
            return False
        return not mapa_ya_en(misiones.POR_ID[mision_id]["ubicacion"])

    def mapa_llegar_directo(ubicacion):
        nodo = MAPA_NOVA.paradas[ubicacion]
        store.mapa_posicion = {"origen": nodo, "destino": nodo, "avance": 0.0}

    def ubicacion_disponible(ubicacion):
        return (not store.modo_feria_activo) or ubicacion in UBICACIONES_FERIA

    def entrar_ubicacion(ubicacion):
        """Gancho de llegada: hoy solo guarda el lugar y avisa."""
        if not ubicacion_disponible(ubicacion):
            return
        store.ubicacion_actual = ubicacion
        sonar("assets/audio/sfx/ui_click.wav")
        mision = mision_actual()
        if mision and mision["ubicacion"] == ubicacion:
            renpy.notify("Llegaste a %s. Aquí transcurre: %s" % (UBICACIONES[ubicacion][0], mision["titulo"]))
        else:
            renpy.notify("Llegaste a %s" % UBICACIONES[ubicacion][0])

    def cargar_cuadros_carro():
        cuadros = {}
        for rumbo in RUMBOS:
            lista, i = [], 0
            while renpy.loadable(MAPA_CARPETA_CARRO % (rumbo, i)):
                imagen = Transform(MAPA_CARPETA_CARRO % (rumbo, i), zoom=MAPA_ZOOM_CARRO, align=(0.5, 0.5))
                lista.append(Fixed(imagen, xysize=MAPA_CAJA_CARRO))
                i += 1
            cuadros[rumbo] = lista
        return cuadros

    class MapaConduccion(renpy.Displayable):
        """El mapa ilustrado con el carro encima. Flechas o WASD conducen; Enter entra al lugar."""

        TECLAS = {
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
        }

        def __init__(self, obligatorio=False, destino=None, **kwargs):
            super(MapaConduccion, self).__init__(**kwargs)
            self.obligatorio = obligatorio
            self.destino = destino
            self.carro = Carro(MAPA_NOVA, MAPA_INICIO)
            if store.mapa_posicion:
                self.carro.restaurar(store.mapa_posicion)
            self.fondo = Transform(MAPA_IMAGEN, zoom=MAPA_ZOOM_IMAGEN)
            self.cuadros = cargar_cuadros_carro()
            self.sombra = Solid("#0000004d")
            self.pulsadas = []
            self.previo = None
            self.camara = None
            self.cerca = self.carro.ubicacion_cercana()
            self.cerca_avisada = self.cerca
            self.depurar = False

        def guardar(self):
            store.mapa_posicion = self.carro.estado()

        # ----- dibujo -----

        def direccion(self):
            dx = dy = 0
            for tecla in self.pulsadas:
                ax, ay = self.TECLAS[tecla]
                dx, dy = (ax or dx), (ay or dy)
            return dx, dy

        def render(self, width, height, st, at):
            dt = 0.0 if self.previo is None else min(0.05, st - self.previo)
            self.previo = st
            dx, dy = self.direccion()
            self.carro.avanzar(dt, dx, dy)
            self.cerca = self.carro.ubicacion_cercana()

            x, y = self.carro.posicion()
            objetivo = max(0.0, min(y * MAPA_ESCALA - height / 2.0, ALTO_REF * MAPA_ESCALA - height))
            if self.camara is None:
                self.camara = objetivo
            self.camara += (objetivo - self.camara) * min(1.0, dt * 5.0)

            r = renpy.Render(width, height)
            r.blit(renpy.render(self.fondo, width, height, st, at), (0, -int(self.camara)))
            self.dibujar_apagadas(r)
            self.dibujar_destino(r, st, width, height)
            if self.depurar:
                self.dibujar_calles(r)

            px, py = x * MAPA_ESCALA, y * MAPA_ESCALA - self.camara
            cuadros = self.cuadros[self.carro.rumbo]
            if cuadros:
                indice = int(st * MAPA_CUADROS_POR_SEGUNDO) % len(cuadros) if self.carro.velocidad > 1.0 else 0
                cw, ch = MAPA_CAJA_CARRO
                r.blit(renpy.render(self.sombra, 70, 18, st, at), (int(px - 35), int(py + 6)))
                r.blit(renpy.render(cuadros[indice], cw, ch, st, at), (int(px - cw / 2), int(py - ch * 0.62)))
            renpy.redraw(self, 0)
            return r

        def dibujar_apagadas(self, r):
            """En el Modo Feria los lugares fuera de la feria se ven atenuados."""
            lienzo = r.canvas()
            for ubicacion, (nombre, descripcion, centro) in UBICACIONES.items():
                if not ubicacion_disponible(ubicacion):
                    cx, cy = centro[0] * MAPA_ESCALA, centro[1] * MAPA_ESCALA - self.camara
                    lienzo.rect((18, 13, 28, 175), (int(cx - 140), int(cy - 34), 280, 68))

        def dibujar_destino(self, r, st, width, height):
            """Aro pulsante sobre el lugar de la mision activa; si esta fuera de pantalla, una flecha en el borde."""
            mision = mision_destino()
            if not mision or mision["ubicacion"] not in MAPA_NOVA.paradas:
                return
            sx, sy = MAPA_NOVA.pos[MAPA_NOVA.paradas[mision["ubicacion"]]]
            cx, cy = sx * MAPA_ESCALA, sy * MAPA_ESCALA - self.camara
            lienzo = r.canvas()
            if 90 <= cy <= height - 20:
                pulso = (st * 1.6) % 1.0
                lienzo.circle((250, 204, 21, int(230 * (1.0 - pulso))), (int(cx), int(cy)), int(26 + 46 * pulso), 4)
                lienzo.circle((250, 204, 21, 255), (int(cx), int(cy)), 11)
                lienzo.circle((18, 13, 28, 255), (int(cx), int(cy)), 11, 3)
                lienzo.polygon((250, 204, 21, 255), [(cx - 14, cy - 58), (cx + 14, cy - 58), (cx, cy - 34)])
            else:
                arriba = cy < 90
                y = 110 if arriba else height - 40
                dy = -16 if arriba else 16
                x = max(40, min(width - 40, cx))
                lienzo.polygon((250, 204, 21, 255), [(x - 18, y - dy), (x + 18, y - dy), (x, y + dy)])

        def dibujar_calles(self, r):
            lienzo = r.canvas()
            for a, b in MAPA_NOVA.aristas():
                (xa, ya), (xb, yb) = MAPA_NOVA.pos[a], MAPA_NOVA.pos[b]
                lienzo.line((255, 60, 60, 255), (xa * MAPA_ESCALA, ya * MAPA_ESCALA - self.camara),
                            (xb * MAPA_ESCALA, yb * MAPA_ESCALA - self.camara), 3)
            for nodo, (nx, ny) in MAPA_NOVA.pos.items():
                color = (60, 255, 90, 255) if MAPA_NOVA.ubicacion_de_nodo(nodo) else (255, 230, 60, 255)
                lienzo.circle(color, (int(nx * MAPA_ESCALA), int(ny * MAPA_ESCALA - self.camara)), 6)

        # ----- entrada -----

        def event(self, ev, x, y, st):
            if ev.type == pygame.KEYDOWN:
                if ev.key in self.TECLAS:
                    if ev.key in self.pulsadas:
                        self.pulsadas.remove(ev.key)
                    self.pulsadas.append(ev.key)
                    raise renpy.IgnoreEvent()
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    if self.cerca and self.obligatorio:
                        return self.llegar(self.cerca)
                    if self.cerca:
                        entrar_ubicacion(self.cerca)
                    raise renpy.IgnoreEvent()
                if ev.key == pygame.K_F9 and config.developer:
                    self.depurar = not self.depurar
                    raise renpy.IgnoreEvent()
            elif ev.type == pygame.KEYUP and ev.key in self.TECLAS:
                if ev.key in self.pulsadas:
                    self.pulsadas.remove(ev.key)
                raise renpy.IgnoreEvent()
            if self.cerca != self.cerca_avisada:
                self.cerca_avisada = self.cerca
                renpy.restart_interaction()
            return None

        def llegar(self, ubicacion):
            """Viaje obligatorio: solo el lugar de la mision termina la interaccion."""
            if ubicacion == self.destino:
                self.guardar()
                sonar("assets/audio/sfx/ui_click.wav")
                return "llegada"
            mision = mision_destino()
            if mision:
                renpy.notify("Aquí todavía no pasa nada. Tu misión: %s, en %s." % (
                    mision["titulo"], UBICACIONES[mision["ubicacion"]][0]))
            raise renpy.IgnoreEvent()

        def visit(self):
            return [self.fondo]


style mapa_texto is default:
    color "#fbf6ee"

screen mapa_ciudad():
    zorder 103
    modal True
    default vista = MapaConduccion()
    on "hide" action Function(vista.guardar)
    key "game_menu" action Hide("mapa_ciudad")

    add vista
    use mapa_cuerpo(vista, False)

## Viaje de la historia: debajo del HUD (zorder 50) para poder consultar pistas, y sin boton de volver.
screen mapa_viaje(destino):
    zorder 40
    modal True
    default vista = MapaConduccion(obligatorio=True, destino=destino)

    add vista
    use mapa_cuerpo(vista, True)

screen mapa_cuerpo(vista, obligatorio):
    ## Barra superior
    frame:
        xfill True
        ysize 76
        padding (40, 10, 40, 10)
        background Solid("#120d1ceb")
        hbox:
            xfill True
            yalign 0.5
            vbox:
                yalign 0.5
                text "MAPA" size 16 color "#a7a5f2" kerning 3
                text "Ciudad Nova" size 32 bold True style "mapa_texto"
            if not obligatorio:
                button:
                    xalign 1.0
                    yalign 0.5
                    xsize 138
                    ysize 44
                    background Frame("gui/telefono_boton.png", 30, 30)
                    hover_background Frame("gui/telefono_boton_hover.png", 30, 30)
                    hover_sound "assets/audio/sfx/ui_hover.wav"
                    activate_sound "assets/audio/sfx/ui_click.wav"
                    action Hide("mapa_ciudad")
                    text "Volver" size 16 bold True color "#fbf6ee" align (0.5, 0.5)

    ## Mision activa
    $ mision = mision_destino()
    $ destino_nombre = UBICACIONES[mision["ubicacion"]][0] if mision else ""
    frame:
        xalign 1.0
        xoffset -36
        ypos 100
        xsize 520
        padding (24, 18)
        background Solid("#120d1ceb")
        vbox:
            spacing 6
            text ("VIAJE · MISIÓN PRINCIPAL" if obligatorio else "MISIÓN PRINCIPAL") size 14 color "#facc15" kerning 3
            if mision:
                text mision["titulo"] size 26 bold True style "mapa_texto"
                text mision["descripcion"] size 18 color "#c9b8d8"
                null height 4
                text "Destino: [destino_nombre]" size 18 bold True color "#a7a5f2"
            else:
                text "Sin misiones pendientes" size 22 bold True style "mapa_texto"
                text "Explora la ciudad cuando quieras." size 18 color "#c9b8d8"

    ## Controles
    frame:
        xpos 40
        yalign 1.0
        yoffset -40
        padding (24, 16)
        background Solid("#120d1ceb")
        vbox:
            spacing 6
            text "CONTROLES" size 14 color "#a7a5f2" kerning 3
            text "Flechas o WASD: conducir" size 20 style "mapa_texto"
            text ("Enter: llegar al destino" if obligatorio else "Enter: entrar al lugar") size 20 style "mapa_texto"
            text ("Esc: menú" if obligatorio else "Esc: volver") size 20 style "mapa_texto"

    ## Tarjeta del lugar cercano
    if vista.cerca:
        $ nombre_lugar, texto_lugar, _centro = UBICACIONES[vista.cerca]
        $ disponible = ubicacion_disponible(vista.cerca)
        frame:
            xalign 0.5
            yalign 1.0
            yoffset -40
            xsize 640
            padding (28, 18)
            background Solid("#120d1cf2")
            vbox:
                spacing 4
                xalign 0.5
                text nombre_lugar.upper() size 30 bold True color "#fbf6ee" xalign 0.5 kerning 2
                text texto_lugar size 20 color "#c9b8d8" xalign 0.5
                null height 6
                if disponible and mision and mision["ubicacion"] == vista.cerca:
                    text "Es el destino de tu misión · Pulsa Enter" size 20 bold True color "#facc15" xalign 0.5
                elif obligatorio:
                    text "Aquí no pasa nada por ahora" size 20 bold True color "#c9b8d8" xalign 0.5
                elif disponible:
                    text "Pulsa Enter para entrar" size 20 bold True color "#a7a5f2" xalign 0.5
                else:
                    text "No disponible en el Modo Feria" size 20 bold True color "#e86a7e" xalign 0.5


## La historia llama a este label antes de cada escena que ocurre en un lugar del mapa.
## Si el carro ya esta ahi (o la feria no pide conducir ese tramo) llega directo.
label viajar_a_mision(mision_id):
    $ mapa_objetivo = mision_id
    $ lugar_viaje = misiones.POR_ID[mision_id]["ubicacion"]
    if mapa_debe_conducir(mision_id):
        $ ocultar_avisos_juego()
        show screen hud_ciudad
        window hide
        $ quick_menu_previo = quick_menu
        $ quick_menu = False
        $ renpy.notify("Nueva misión: %s" % misiones.POR_ID[mision_id]["titulo"])
        call screen mapa_viaje(lugar_viaje)
        $ quick_menu = quick_menu_previo
        window auto
    else:
        $ mapa_llegar_directo(lugar_viaje)
    $ ubicacion_actual = lugar_viaje
    $ mapa_objetivo = None
    return
