## Animacion de la propagacion BFS nivel por nivel.
## Uso:  call animar_propagacion(origen="jugador", semilla=7, factor=1.5)
## Retorna (en _return) la lista de niveles calculada por bfs_propagacion().

define sfx_nodo_activado = "assets/audio/sfx/nodo_activado.wav"

init python:

    def sonar_nodo():
        if renpy.loadable(sfx_nodo_activado):
            renpy.sound.play(sfx_nodo_activado)

    def vista_bfs(grafo, niveles, padres, paso, estado_activo):
        """Estados de nodos/aristas cuando ya se revelaron 'paso' niveles."""
        nivel_de = {}
        for i, nivel in enumerate(niveles):
            for nodo in nivel:
                nivel_de[nodo] = i
        estados, efectos, subtitulos, resaltadas = {}, {}, {}, {}
        color_arista = COLOR_ESTADO[estado_activo]
        for nodo in grafo.lista_nodos():
            nivel = nivel_de.get(nodo)
            if nivel is None:
                estados[nodo] = "apagado" if paso >= len(niveles) else "normal"
            elif nivel < paso:
                estados[nodo] = estado_activo
                efectos[nodo] = "pop"
                subtitulos[nodo] = "N%d" % nivel
                if nodo in padres:
                    resaltadas[(padres[nodo], nodo)] = color_arista
            elif nivel == paso:
                estados[nodo] = "cola"
                efectos[nodo] = "pulso"
        return estados, efectos, subtitulos, resaltadas


screen propagacion_bfs(grafo, niveles, padres, titulo, estado_activo="activo", delay=1.0):
    modal True
    zorder 40

    default paso = 1
    $ pos = posiciones_grafo(grafo)
    $ estados, efectos, subtitulos, resaltadas = vista_bfs(grafo, niveles, padres, paso, estado_activo)
    $ terminado = paso >= len(niveles)
    $ alcanzados = sum(len(nivel) for nivel in niveles[:paso])
    $ total_nodos = grafo.cantidad_nodos()
    $ total_niveles = len(niveles)

    add (FONDO_RASTREADOR if estado_activo == "verificado" else FONDO_CONTENCION)
    use grafo_red(grafo, pos, estados, efectos, {}, resaltadas, subtitulos)

    text titulo pos (40, 48) size 34 color "#38bdf8" bold True
    use leyenda_grafo([("normal", "Sin alcanzar"), ("cola", "En cola"), (estado_activo, "Alcanzado"), ("apagado", "No llego")])

    if not terminado:
        timer delay repeat True action [SetScreenVariable("paso", paso + 1), Function(sonar_nodo)]

    frame:
        style_prefix "grafo"
        xpos 1270
        ypos 60
        xsize 640
        vbox:
            text "Recorrido BFS por niveles" size 28 color "#f8fafc" bold True
            text "Cola FIFO: se visita todo un nivel antes de pasar al siguiente. Los visitados no se repiten." size 18 color "#94a3b8"
            null height 6

            if not niveles:
                text "La publicacion no tiene desde donde propagarse."

            for i in range(min(paso, len(niveles))):
                hbox at fila_entrada:
                    text "Nivel [i]" size 22 color COLOR_ESTADO[estado_activo] bold True min_width 110
                    text nombres(grafo, niveles[i]) size 20 xmaximum 380

            if not terminado:
                hbox:
                    text "En cola" size 22 color "#fbbf24" bold True min_width 110
                    text nombres(grafo, niveles[paso]) size 20 color "#fbbf24" xmaximum 380

            null height 6
            text "Usuarios alcanzados: [alcanzados] de [total_nodos]" size 24 color "#f8fafc"

            if terminado:
                text "Propagacion terminada en [total_niveles] nivel(es)." size 20 color "#94a3b8"
                null height 6
                textbutton "Repetir animacion" action SetScreenVariable("paso", 1)
                textbutton "Continuar" action Return()


label animar_propagacion(origen="jugador", titulo="Propagacion en Civitas", semilla=None, factor=1.0, estado_activo="activo", delay=1.0):
    $ padres_bfs = {}
    $ niveles_bfs = red_civitas.bfs_propagacion(origen, semilla=semilla, factor=factor, padres=padres_bfs)
    call screen propagacion_bfs(red_civitas, niveles_bfs, padres_bfs, titulo, estado_activo, delay)
    return niveles_bfs
