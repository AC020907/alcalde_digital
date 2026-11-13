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

    # ===== BUSQUEDA, ELIMINACION Y MEDIDAS =====

    def buscar(self, etiqueta, nodo=None):
        """DFS en preorden: primer nodo cuya etiqueta (o texto) coincide. None si no existe."""
        nodo = self.raiz if nodo is None else nodo
        if nodo is None:
            return None
        if nodo.etiqueta == etiqueta or nodo.texto == etiqueta:
            return nodo
        for hijo in nodo.hijos:
            hallado = self.buscar(etiqueta, hijo)
            if hallado is not None:
                return hallado
        return None

    def eliminar(self, nodo):
        """Quita 'nodo' y todo su subarbol (una opcion deja de existir). Eliminar la raiz vacia el arbol."""
        if nodo is None:
            return False
        if nodo is self.raiz:
            self.raiz = None
            return True
        if nodo.padre is None or nodo not in nodo.padre.hijos:
            return False
        nodo.padre.quitar_hijo(nodo)
        return True

    def recorrer_ruta(self, indices):
        """Sigue una ruta de indices desde la raiz. Retorna los nodos visitados, o None si la ruta es invalida."""
        if self.raiz is None:
            return None
        nodo, visitados = self.raiz, [self.raiz]
        for i in indices:
            if not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < len(nodo.hijos):
                return None
            nodo = nodo.hijos[i]
            visitados.append(nodo)
        return visitados

    def hojas(self, nodo=None):
        nodo = self.raiz if nodo is None else nodo
        if nodo is None:
            return []
        if nodo.es_hoja():
            return [nodo]
        return [h for hijo in nodo.hijos for h in self.hojas(hijo)]

    def altura(self, nodo=None):
        nodo = self.raiz if nodo is None else nodo
        if nodo is None:
            return 0
        return 1 + max([self.altura(h) for h in nodo.hijos] or [0])

    def tamanio(self, nodo=None):
        nodo = self.raiz if nodo is None else nodo
        if nodo is None:
            return 0
        return 1 + sum(self.tamanio(h) for h in nodo.hijos)
