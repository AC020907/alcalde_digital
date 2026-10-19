from collections import deque
import math
import random


class GrafoSocial:
    """
    Red social Civitas como grafo dirigido y pesado (lista de adyacencia).

    - Nodo: un usuario de Civitas.
    - Arista origen -> destino: lo que publica 'origen' le llega a 'destino'.
    - Peso (0..1): fuerza o probabilidad de que la publicacion se propague
      por esa conexion.
    """

    def __init__(self):
        self.adyacencia = {}   # nodo -> {vecino: peso}       (aristas salientes)
        self.entrantes = {}    # nodo -> {predecesor: peso}   (aristas entrantes)
        self.datos = {}        # nodo -> {"nombre", "tipo", "alcance"}

    # ===== CONSTRUCCION =====

    def agregar_usuario(self, nodo, nombre=None, tipo="ciudadano", alcance=1, perfil=None):
        if nodo in self.adyacencia:
            return
        self.adyacencia[nodo] = {}
        self.entrantes[nodo] = {}
        self.datos[nodo] = {"nombre": nombre or nodo, "tipo": tipo, "alcance": alcance,
                            "perfil": perfil or {}}

    def agregar_conexion(self, origen, destino, peso=1.0):
        if origen == destino:
            return
        self.agregar_usuario(origen)
        self.agregar_usuario(destino)
        peso = max(0.0, min(1.0, float(peso)))
        self.adyacencia[origen][destino] = peso
        self.entrantes[destino][origen] = peso

    # ===== CONSULTAS =====

    def existe(self, nodo):
        return nodo in self.adyacencia

    def lista_nodos(self):
        return list(self.adyacencia)

    def cantidad_nodos(self):
        return len(self.adyacencia)

    def vecinos(self, nodo):
        return list(self.adyacencia.get(nodo, {}))

    def predecesores(self, nodo):
        return list(self.entrantes.get(nodo, {}))

    def peso(self, origen, destino):
        return self.adyacencia.get(origen, {}).get(destino, 0.0)

    def existe_conexion(self, origen, destino):
        return destino in self.adyacencia.get(origen, {})

    def aristas(self):
        resultado = []
        for origen in self.adyacencia:
            for destino, peso in self.adyacencia[origen].items():
                resultado.append((origen, destino, peso))
        return resultado

    def grado_salida(self, nodo):
        return len(self.adyacencia.get(nodo, {}))

    def grado_entrada(self, nodo):
        return len(self.entrantes.get(nodo, {}))

    def nombre(self, nodo):
        return self.datos[nodo]["nombre"]

    def tipo(self, nodo):
        return self.datos[nodo]["tipo"]

    def alcance(self, nodo):
        return self.datos[nodo]["alcance"]

    def perfil(self, nodo):
        return self.datos[nodo]["perfil"]

    # ===== POSICIONAMIENTO CIRCULAR (para dibujar) =====

    def posiciones_circulares(self, centro_x, centro_y, radio, nodo_central=None):
        """
        Reparte los nodos en un circulo: el nodo i queda en el angulo
        2*pi*i/n, empezando arriba (-pi/2). Opcionalmente un nodo va al centro.
        Retorna {nodo: (x, y)}.
        """
        posiciones = {}
        if nodo_central in self.adyacencia:
            posiciones[nodo_central] = (centro_x, centro_y)

        anillo = [n for n in self.adyacencia if n != nodo_central]
        total = len(anillo)
        if total == 1 and not posiciones:
            posiciones[anillo[0]] = (centro_x, centro_y)
            return posiciones

        for i, nodo in enumerate(anillo):
            angulo = 2 * math.pi * i / total - math.pi / 2
            x = centro_x + radio * math.cos(angulo)
            y = centro_y + radio * math.sin(angulo)
            posiciones[nodo] = (int(round(x)), int(round(y)))
        return posiciones

    # ===== PROPAGACION =====

    def se_propaga(self, origen, destino, semilla=None, factor=1.0):
        """
        Decide si la publicacion cruza la arista origen -> destino.
        - semilla None: modo determinista, toda conexion existente propaga.
        - con semilla: probabilistico, propaga si el "dado" de esa arista
          sale menor que peso * factor. El dado depende solo de
          (semilla, origen, destino): misma semilla => mismo resultado.
        """
        probabilidad = min(1.0, self.peso(origen, destino) * factor)
        if probabilidad <= 0:
            return False
        if semilla is None:
            return True
        dado = random.Random("%s|%s|%s" % (semilla, origen, destino)).random()
        return dado < probabilidad

    def bfs_propagacion(self, origen, semilla=None, factor=1.0, bloqueados=None, padres=None):
        """
        BFS desde 'origen' usando una cola. Retorna la propagacion por niveles:
            [[origen], [nivel 1...], [nivel 2...], ...]
        - visitados evita repetir nodos (y ciclos infinitos).
        - bloqueados: nodos que no pueden recibir la publicacion.
        - padres (dict opcional): se llena con padres[nodo] = quien se lo envio.
        """
        if origen not in self.adyacencia:
            return []
        if bloqueados is None:
            bloqueados = set()
        if origen in bloqueados:
            return []

        niveles = []
        visitados = set([origen])
        cola = deque()
        cola.append((origen, 0))

        while cola:
            nodo, nivel = cola.popleft()
            if nivel == len(niveles):
                niveles.append([])
            niveles[nivel].append(nodo)

            for vecino in self.adyacencia[nodo]:
                if vecino in visitados or vecino in bloqueados:
                    continue
                if not self.se_propaga(nodo, vecino, semilla, factor):
                    continue
                visitados.add(vecino)
                if padres is not None:
                    padres[vecino] = nodo
                cola.append((vecino, nivel + 1))

        return niveles

    def bfs_recorrido(self, origen):
        return [nodo for nivel in self.bfs_propagacion(origen) for nodo in nivel]

    def propagar_un_paso(self, activos, bloqueados=None, semilla=None, factor=1.0, padres=None,
                         modificadores=None):
        """
        Avanza la propagacion UN nivel (un turno): retorna los nodos nuevos
        que reciben la publicacion desde los nodos activos.
        modificadores: {nodo: multiplicador} aplicado a la probabilidad de llegar a ese nodo.
        """
        if bloqueados is None:
            bloqueados = set()
        nuevos = []
        for nodo in self.adyacencia:
            if nodo not in activos:
                continue
            for vecino in self.adyacencia[nodo]:
                if vecino in activos or vecino in bloqueados or vecino in nuevos:
                    continue
                factor_vecino = factor * (modificadores.get(vecino, 1.0) if modificadores else 1.0)
                if self.se_propaga(nodo, vecino, semilla, factor_vecino):
                    nuevos.append(vecino)
                    if padres is not None:
                        padres[vecino] = nodo
        return nuevos

    # ===== DFS =====

    def dfs_buscar(self, origen, objetivo=None, reverso=False, permitidos=None, condicion=None):
        """
        DFS recursivo desde 'origen'. Sigue una cadena de conexiones hasta
        hallar 'objetivo'; marca visitados para no caer en ciclos.
        - reverso True: recorre aristas al reves (hacia quien envio la publicacion).
        - permitidos: si se da, solo se visitan esos nodos.
        - condicion(nodo, vecino): si se da, solo se avanza cuando retorna True.
        Retorna (camino, orden_visita). camino = [] si no se encontro.
        """
        if origen not in self.adyacencia:
            return [], []

        visitados = set()
        orden = []
        camino = []

        def visitar(nodo):
            visitados.add(nodo)
            orden.append(nodo)
            camino.append(nodo)
            if nodo == objetivo:
                return True
            siguientes = self.predecesores(nodo) if reverso else self.vecinos(nodo)
            for vecino in siguientes:
                if vecino in visitados:
                    continue
                if permitidos is not None and vecino not in permitidos:
                    continue
                if condicion is not None and not condicion(nodo, vecino):
                    continue
                if visitar(vecino):
                    return True
            camino.pop()
            return False

        encontrado = visitar(origen)
        return (camino if encontrado else []), orden
