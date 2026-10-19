## MODO SUSTENTACION: vista tecnica (grafo, BFS, DFS) para explicar el codigo.
## El jugador normal nunca la ve. Se activa desde el laboratorio (Shift+L) y
## agrega un boton "RED INTERNA" en los minijuegos (el juego se pausa).

default modo_sustentacion = False

init python:

    def vista_debug_arcade(sim):
        estados, resaltadas, subtitulos = {}, {}, {}
        rastreo = isinstance(sim, RastreoEnVivo)
        for nodo, estado in sim.estado_nodo.items():
            if estado == "inmune":
                estados[nodo] = "apagado"
            elif estado == "infectado":
                estados[nodo] = "infectado"
            elif estado == "cuarentena":
                estados[nodo] = "visitado"
            elif estado == "protegido":
                estados[nodo] = "contenido"
            elif nodo in sim.en_camino:
                estados[nodo] = "riesgo"
            if nodo in sim.hora:
                subtitulos[nodo] = "t=%.0fs" % sim.hora[nodo]
        for paquete in sim.paquetes:
            resaltadas[(paquete.origen, paquete.destino)] = "#f97316"
        ruta = []
        if rastreo:
            for nodo in sim.rastro:
                estados[nodo] = "pila"
            estados[sim.actual()] = "actual"
            estados[sim.origen] = "origen"
            ruta = sim.ruta_al_origen()
            for i in range(len(ruta) - 1):
                resaltadas[(ruta[i + 1], ruta[i])] = "#c084fc"
            for i in range(len(sim.rastro) - 1):
                resaltadas[(sim.rastro[i + 1], sim.rastro[i])] = "#facc15"
        return estados, resaltadas, subtitulos, ruta


screen debug_arcade(sim):
    modal True
    zorder 170
    $ g = sim.grafo
    $ pos = posiciones_grafo(g)
    $ rastreo = isinstance(sim, RastreoEnVivo)
    $ estados, resaltadas, subtitulos, ruta = vista_debug_arcade(sim)

    add Solid("#020617f8")
    use grafo_red(g, pos, estados, {}, {}, resaltadas, subtitulos)
    text ("MODO SUSTENTACION - Rastreador (DFS + BFS)" if rastreo else "MODO SUSTENTACION - BFS en tiempo real") pos (40, 48) size 30 color "#facc15" bold True
    use leyenda_grafo([("infectado", "Comparte"), ("riesgo", "Rumor en camino"), ("visitado", "Cuarentena"), ("contenido", "Protegida"), ("pila", "Pila DFS"), ("origen", "Origen")])

    frame:
        style_prefix "grafo"
        xpos 1270
        ypos 60
        xsize 640
        vbox:
            text "Grafo dirigido y pesado" size 22 bold True color "#f8fafc"
            text "[g.cantidad_nodos()] usuarios. Peso de la arista = probabilidad y velocidad del contagio." size 16
            null height 6
            text "BFS: cola FIFO procesada en tiempo real" size 20 bold True color "#38bdf8"
            text "Cola: " + (", ".join(g.nombre(n) for n, _ in sim.cola) or "vacia") size 15
            text "Rumores en vuelo (aristas recorridas): %d" % len(sim.paquetes) size 15
            text "Visitados (contagiados): %d" % len(sim.hora) size 15
            if rastreo:
                null height 6
                text "DFS: rastro del jugador como pila" size 20 bold True color "#facc15"
                text "Pila (base -> tope): " + " > ".join(g.nombre(n) for n in sim.rastro) size 15
                text "dfs_buscar (reverso) hasta el origen:" size 17 bold True color "#c084fc"
                text " > ".join(g.nombre(n) for n in ruta) size 15
            null height 10
            textbutton "CERRAR Y CONTINUAR" action Hide("debug_arcade")
