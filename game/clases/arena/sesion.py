"""Objetos vivos de la Arena en la interfaz (sockets, hilos). Viven aqui y no en el store de Ren'Py para
que nunca entren en una partida guardada ni en el rollback."""
servidor = None
clave = None
cliente = None
bots = []
empezar_pendiente = False   # el anfitrion pidio empezar y faltan bots por estar listos
ruta = []              # ruta elegida dentro del arbol de la ronda actual
ronda_vista = None     # numero de ronda que la interfaz ya anuncio
resultado_visto = None
final_visto = False
modo = "completo"     # "clasica" | "completo" | "feria" (torneo de minijuegos)
prueba_jugada = None   # indice de la prueba del torneo que este cliente ya jugo
resumen_visto = None
aviso_tiempo = None
grafo_fuente = None
grafo = None           # GrafoSocial reconstruido desde el servidor (para dibujar)
posiciones = {}
