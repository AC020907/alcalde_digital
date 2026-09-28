from collections import deque
from clases.Node import NodoDecision


class ArbolDecisiones:

    def __init__(self):
        self.raiz = None

    def insertar_raiz(self, texto):
        self.raiz = NodoDecision(texto)
        return self.raiz

    def insertar_hijo(self, padre, texto, consecuencia=None, etiqueta=None):
        hijo = NodoDecision(texto, consecuencia, etiqueta)
        padre.agregar_hijo(hijo)
        return hijo

    # ===== RECORRIDOS =====

    def preorden(self, nodo, resultado=None):
        if resultado is None:
            resultado = []
        if nodo is None:
            return resultado
        resultado.append(nodo.texto)
        for hijo in nodo.hijos:
            self.preorden(hijo, resultado)
        return resultado

    def posorden(self, nodo, resultado=None):
        if resultado is None:
            resultado = []
        if nodo is None:
            return resultado
        for hijo in nodo.hijos:
            self.posorden(hijo, resultado)
        resultado.append(nodo.texto)
        return resultado

    def recorrido_por_niveles(self):
        if not self.raiz:
            return []
        resultado = []
        cola = deque([self.raiz])
        while cola:
            nodo_actual = cola.popleft()
            resultado.append(nodo_actual.texto)
            for hijo in nodo_actual.hijos:
                cola.append(hijo)
        return resultado

    def avanzar(self, nodo_actual, indice):
        return nodo_actual.hijos[indice]
