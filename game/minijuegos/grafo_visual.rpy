## Presentacion del grafo social Civitas.
## La logica vive en clases/GrafoSocial.py; aqui solo se dibuja.

init python:
    import math
    from clases.GrafoSocial import GrafoSocial
    from clases.RedCivitas import crear_red_civitas, ORIGEN_RUMOR

    GRAFO_CENTRO = (640, 560)
    GRAFO_RADIO = 400
    GRAFO_ANCHO_CAPA = 1260
    GRAFO_ALTO_CAPA = 1080

    COLOR_ESTADO = {
        "normal":     "#334155",
        "apagado":    "#111827",
        "activo":     "#f97316",
        "verificado": "#16a34a",
        "cola":       "#78350f",
        "infectado":  "#dc2626",
        "contenido":  "#0284c7",
        "riesgo":     "#b45309",
        "pila":       "#c2410c",
        "actual":     "#eab308",
        "candidato":  "#0e7490",
        "visitado":   "#475569",
        "origen":     "#9333ea",
    }

    ICONO_TIPO = {
        "jugador":    "assets/ui/nodo_jugador.png",
        "medio":      "assets/ui/nodo_medio.png",
        "influencer": "assets/ui/nodo_influencer.png",
        "ciudadano":  "assets/ui/nodo_ciudadano.png",
        "bot":        "assets/ui/nodo_bot.png",
    }

    FONDO_RASTREADOR = "assets/backgrounds/fondo_rastreador.jpg"
    FONDO_CONTENCION = "assets/backgrounds/fondo_contencion.jpg"
    FONDO_VIRALIZACION = "assets/backgrounds/fondo_viralizacion.jpg"

    # Estados en los que el usuario queda fuera del juego: el icono se atenua.
    ESTADOS_ATENUADOS = {"apagado": 0.3, "visitado": 0.55}
    GROSOR_ANILLO = 6

    def rgba(hexa, alfa=255):
        hexa = hexa.lstrip("#")
        return (int(hexa[0:2], 16), int(hexa[2:4], 16), int(hexa[4:6], 16), alfa)

    def aclarar(hexa, cantidad=50):
        r, g, b, _ = rgba(hexa)
        return "#%02x%02x%02x" % (min(255, r + cantidad), min(255, g + cantidad), min(255, b + cantidad))

    def posiciones_grafo(grafo):
        return grafo.posiciones_circulares(GRAFO_CENTRO[0], GRAFO_CENTRO[1], GRAFO_RADIO, nodo_central="jugador")

    def radio_nodo(grafo, nodo):
        if grafo.tipo(nodo) == "jugador":
            return 40
        return int(28 + min(grafo.alcance(nodo), 60) * 0.25)

    def icono_nodo(grafo, nodo, estado, radio):
        lado = (radio - GROSOR_ANILLO) * 2
        return Transform(ICONO_TIPO[grafo.tipo(nodo)], xysize=(lado, lado),
                         alpha=ESTADOS_ATENUADOS.get(estado, 1.0))

    class CirculoNodo(renpy.Displayable):
        # Se dibuja 3 veces mas grande y se reduce con zoom para suavizar el borde.
        ESCALA = 3
        cache = {}

        def __init__(self, relleno, borde, radio, **kwargs):
            super(CirculoNodo, self).__init__(**kwargs)
            self.relleno = relleno
            self.borde = borde
            self.radio = radio

        def render(self, width, height, st, at):
            e = self.ESCALA
            lado = self.radio * 2 * e
            r = renpy.Render(lado, lado)
            lienzo = r.canvas()
            centro = (self.radio * e, self.radio * e)
            lienzo.circle(rgba(self.borde), centro, self.radio * e)
            lienzo.circle(rgba(self.relleno), centro, (self.radio - 4) * e)
            return r

    def circulo(relleno, borde, radio):
        clave = (relleno, borde, radio)
        if clave not in CirculoNodo.cache:
            CirculoNodo.cache[clave] = Transform(CirculoNodo(relleno, borde, radio), zoom=1.0 / CirculoNodo.ESCALA)
        return CirculoNodo.cache[clave]

    class CapaAristas(renpy.Displayable):
        cache = {}

        def __init__(self, segmentos, ancho, alto, **kwargs):
            super(CapaAristas, self).__init__(**kwargs)
            self.segmentos = segmentos
            self.ancho = ancho
            self.alto = alto

        def render(self, width, height, st, at):
            r = renpy.Render(self.ancho, self.alto)
            lienzo = r.canvas()
            for x1, y1, x2, y2, color, grosor in self.segmentos:
                lienzo.line(color, (x1, y1), (x2, y2), grosor)
                angulo = math.atan2(y2 - y1, x2 - x1)
                largo = 10 + grosor * 2
                p1 = (x2 - largo * math.cos(angulo - 0.42), y2 - largo * math.sin(angulo - 0.42))
                p2 = (x2 - largo * math.cos(angulo + 0.42), y2 - largo * math.sin(angulo + 0.42))
                lienzo.polygon(color, [(x2, y2), p1, p2])
            return r

    def capa_aristas(grafo, pos, resaltadas=None, atenuar=()):
        """resaltadas: {(origen, destino): color}. Cada arista se acorta para terminar en el borde del nodo."""
        resaltadas = resaltadas or {}
        segmentos = []
        for origen, destino, peso in grafo.aristas():
            x1, y1 = pos[origen]
            x2, y2 = pos[destino]
            distancia = math.hypot(x2 - x1, y2 - y1)
            if distancia == 0:
                continue
            ux, uy = (x2 - x1) / distancia, (y2 - y1) / distancia
            ox, oy = 0.0, 0.0
            if grafo.existe_conexion(destino, origen):
                ox, oy = -uy * 6, ux * 6
            r1 = radio_nodo(grafo, origen)
            r2 = radio_nodo(grafo, destino) + 3
            if (origen, destino) in resaltadas:
                color = rgba(resaltadas[(origen, destino)])
                grosor = 5
            else:
                alfa = 35 if (origen in atenuar or destino in atenuar) else int(60 + 130 * peso)
                color = rgba("#94a3b8", alfa)
                grosor = 1 + int(round(peso * 3))
            segmentos.append((int(x1 + ux * r1 + ox), int(y1 + uy * r1 + oy),
                              int(x2 - ux * r2 + ox), int(y2 - uy * r2 + oy), color, grosor))
        segmentos.sort(key=lambda s: s[5])
        clave = tuple(segmentos)
        if clave not in CapaAristas.cache:
            if len(CapaAristas.cache) > 60:
                CapaAristas.cache.clear()
            CapaAristas.cache[clave] = CapaAristas(segmentos, GRAFO_ANCHO_CAPA, GRAFO_ALTO_CAPA)
        return CapaAristas.cache[clave]

    def efecto_nodo(nombre):
        if nombre == "pop":
            return nodo_pop
        if nombre == "pulso":
            return nodo_pulso
        return nodo_quieto

    def nombres(grafo, nodos):
        return ", ".join(grafo.nombre(n) for n in nodos)


default red_civitas = crear_red_civitas()

transform nodo_quieto:
    zoom 1.0

transform nodo_pop:
    zoom 0.3 alpha 0.2
    easein 0.22 zoom 1.45 alpha 1.0
    easeout 0.25 zoom 1.0

transform nodo_pulso:
    zoom 1.0
    block:
        easein 0.45 zoom 1.18
        easeout 0.45 zoom 1.0
        repeat

transform fila_entrada:
    alpha 0.0 xoffset 30
    easein 0.3 alpha 1.0 xoffset 0

transform resultado_entrada:
    alpha 0.0 zoom 0.85
    easein 0.3 alpha 1.0 zoom 1.0

style grafo_frame is empty:
    # La imagen trae ~45px de brillo transparente alrededor del borde visible.
    background Frame("assets/ui/panel_civitas.png", 100, 100)
    padding (72, 70)

style grafo_vbox:
    spacing 10

style grafo_hbox:
    spacing 10

style grafo_text is default:
    size 22
    color "#cbd5e1"

style grafo_button is default:
    background "#1e293b"
    hover_background "#2563eb"
    insensitive_background "#1e293b66"
    padding (16, 9)
    xfill True

style grafo_button_text is default:
    size 21
    color "#f1f5f9"
    hover_color "#ffffff"
    insensitive_color "#64748b"


## Dibuja el grafo completo. Cada vista (BFS, rastreador, contencion...)
## solo decide el estado/efecto/accion de cada nodo y que aristas resaltar.
screen grafo_red(grafo, pos, estados, efectos={}, acciones={}, resaltadas={}, subtitulos={}, atenuar=()):

    add capa_aristas(grafo, pos, resaltadas, atenuar)

    for nodo in grafo.lista_nodos():
        $ x, y = pos[nodo]
        $ r = radio_nodo(grafo, nodo)
        $ estado = estados.get(nodo, "normal")
        $ anillo = COLOR_ESTADO[estado]

        fixed:
            xysize (r * 2, r * 2)
            pos (x, y)
            anchor (0.5, 0.5)
            at efecto_nodo(efectos.get(nodo))

            button:
                style "empty"
                xysize (r * 2, r * 2)
                background circulo(anillo, aclarar(anillo, 40), r)
                hover_background circulo(aclarar(anillo, 90), "#ffffff", r)
                action acciones.get(nodo)
                add icono_nodo(grafo, nodo, estado, r) align (0.5, 0.5)

        text grafo.nombre(nodo):
            pos (x, y + r + 2)
            xanchor 0.5
            size 17
            color "#e2e8f0"
            outlines [(2, "#000000cc", 0, 0)]

        if nodo in subtitulos:
            text subtitulos[nodo]:
                pos (x, y + r + 22)
                xanchor 0.5
                size 16
                color "#fbbf24"
                outlines [(2, "#000000cc", 0, 0)]


## items: lista de (estado, texto)
screen leyenda_grafo(items):
    hbox:
        pos (40, 98)
        spacing 18
        for estado, texto in items:
            hbox:
                spacing 6
                add circulo(COLOR_ESTADO[estado], aclarar(COLOR_ESTADO[estado], 80), 10) yalign 0.5
                text texto size 17 color "#cbd5e1" yalign 0.5
