from clases.NodoAVL import NodoAVL


class ArbolAVL:

    def __init__(self):
        self.raiz = None
        self.count = 0

    def get_raiz(self):
        return self.raiz

    # ===== ALTURA Y FACTOR DE EQUILIBRIO =====

    def _altura(self, nodo):
        if nodo is None:
            return 0
        return nodo.get_altura()

    def factor_equilibrio(self, nodo):
        if nodo is None:
            return 0
        return self._altura(nodo.get_izquierdo()) - self._altura(nodo.get_derecho())

    def _actualizar_altura(self, nodo):
        nodo.set_altura(1 + max(self._altura(nodo.get_izquierdo()),
                                self._altura(nodo.get_derecho())))

    # ===== ROTACIONES =====

    def _rotacion_der(self, y):      # LL
        x = y.get_izquierdo()
        temp = x.get_derecho()
        x.set_derecho(y)
        y.set_izquierdo(temp)
        self._actualizar_altura(y)
        self._actualizar_altura(x)
        return x

    def _rotacion_izq(self, y):      # RR
        x = y.get_derecho()
        temp = x.get_izquierdo()
        x.set_izquierdo(y)
        y.set_derecho(temp)
        self._actualizar_altura(y)
        self._actualizar_altura(x)
        return x

    # ===== INSERCIÓN =====

    def agregar(self, publicacion):
        self.raiz = self._insertar(self.raiz, publicacion.nivel_riesgo, publicacion)

    def _insertar(self, nodo, clave, pub):
        if nodo is None:
            return NodoAVL(clave, pub)

        if clave < nodo.get_clave():
            nodo.set_izquierdo(self._insertar(nodo.get_izquierdo(), clave, pub))
        elif clave > nodo.get_clave():
            nodo.set_derecho(self._insertar(nodo.get_derecho(), clave, pub))
        else:
            return nodo  # clave duplicada: ignorada

        self._actualizar_altura(nodo)
        balance = self.factor_equilibrio(nodo)

        # LL — rotacion simple derecha
        if balance > 1 and clave < nodo.get_izquierdo().get_clave():
            return self._rotacion_der(nodo)
        # RR — rotacion simple izquierda
        if balance < -1 and clave > nodo.get_derecho().get_clave():
            return self._rotacion_izq(nodo)
        # LR — rotacion doble: izquierda luego derecha
        if balance > 1 and clave > nodo.get_izquierdo().get_clave():
            nodo.set_izquierdo(self._rotacion_izq(nodo.get_izquierdo()))
            return self._rotacion_der(nodo)
        # RL — rotacion doble: derecha luego izquierda
        if balance < -1 and clave < nodo.get_derecho().get_clave():
            nodo.set_derecho(self._rotacion_der(nodo.get_derecho()))
            return self._rotacion_izq(nodo)

        return nodo

    # ===== BÚSQUEDA =====

    def buscar(self, nodo, clave):
        if nodo is None:
            return None
        if clave == nodo.get_clave():
            return nodo
        if clave < nodo.get_clave():
            return self.buscar(nodo.get_izquierdo(), clave)
        return self.buscar(nodo.get_derecho(), clave)

    # ===== ELIMINACIÓN =====

    def borrar(self, clave):
        self.raiz = self._eliminar(self.raiz, clave)

    def _eliminar(self, nodo, clave):
        if nodo is None:
            return None

        if clave < nodo.get_clave():
            nodo.set_izquierdo(self._eliminar(nodo.get_izquierdo(), clave))
        elif clave > nodo.get_clave():
            nodo.set_derecho(self._eliminar(nodo.get_derecho(), clave))
        else:
            # Nodo con un solo hijo o sin hijos
            if nodo.get_izquierdo() is None:
                return nodo.get_derecho()
            elif nodo.get_derecho() is None:
                return nodo.get_izquierdo()
            # Nodo con dos hijos: reemplazar con sucesor inorden (minimo del subárbol derecho)
            sucesor = self._minimo_nodo(nodo.get_derecho())
            nodo.set_clave(sucesor.get_clave())
            nodo.set_publicacion(sucesor.get_publicacion())
            nodo.set_derecho(self._eliminar(nodo.get_derecho(), sucesor.get_clave()))

        self._actualizar_altura(nodo)
        balance = self.factor_equilibrio(nodo)

        # Rebalanceo post-eliminacion
        if balance > 1 and self.factor_equilibrio(nodo.get_izquierdo()) >= 0:
            return self._rotacion_der(nodo)
        if balance > 1 and self.factor_equilibrio(nodo.get_izquierdo()) < 0:
            nodo.set_izquierdo(self._rotacion_izq(nodo.get_izquierdo()))
            return self._rotacion_der(nodo)
        if balance < -1 and self.factor_equilibrio(nodo.get_derecho()) <= 0:
            return self._rotacion_izq(nodo)
        if balance < -1 and self.factor_equilibrio(nodo.get_derecho()) > 0:
            nodo.set_derecho(self._rotacion_der(nodo.get_derecho()))
            return self._rotacion_izq(nodo)

        return nodo

    # ===== NODOS EXTREMOS =====

    def _minimo_nodo(self, nodo):
        actual = nodo
        while actual.get_izquierdo() is not None:
            actual = actual.get_izquierdo()
        return actual

    def maximo_nodo(self, nodo):
        actual = nodo
        while actual.get_derecho() is not None:
            actual = actual.get_derecho()
        return actual

    # ===== RECORRIDOS RECURSIVOS =====

    def preorden(self, nodo):
        if nodo is None:
            return
        print(str(nodo.get_clave()) + "-", end="")
        self.preorden(nodo.get_izquierdo())
        self.preorden(nodo.get_derecho())

    def inorden(self, nodo):
        if nodo is None:
            return
        self.inorden(nodo.get_izquierdo())
        print(str(nodo.get_clave()) + "-", end="")
        self.inorden(nodo.get_derecho())

    def posorden(self, nodo):
        if nodo is None:
            return
        self.posorden(nodo.get_izquierdo())
        self.posorden(nodo.get_derecho())
        print(str(nodo.get_clave()) + "-", end="")

    # ===== RECORRIDOS ITERATIVOS (lista usada como pila: impila=append, campila=pop) =====

    def preorden_iterativo(self, nodo):
        pila = []
        p = nodo
        while p is not None or pila:
            if p is not None:
                print(str(p.get_clave()) + "-", end="")
                self.impila(pila, p)
                p = p.get_izquierdo()
            else:
                p = self.campila(pila)
                p = p.get_derecho()

    def inorden_iterativo(self, nodo):
        pila = []
        p = nodo
        while p is not None or pila:
            if p is not None:
                self.impila(pila, p)
                p = p.get_izquierdo()
            else:
                p = self.campila(pila)
                print(str(p.get_clave()) + "-", end="")
                p = p.get_derecho()

    def posorden_iterativo(self, nodo):
        if nodo is None:
            return
        pila1 = []
        pila2 = []
        self.impila(pila1, nodo)
        while pila1:
            p = self.campila(pila1)
            self.impila(pila2, p)
            if p.get_izquierdo():
                self.impila(pila1, p.get_izquierdo())
            if p.get_derecho():
                self.impila(pila1, p.get_derecho())
        while pila2:
            print(str(self.campila(pila2).get_clave()) + "-", end="")

    def impila(self, pila, p):
        pila.append(p)

    def campila(self, pila):
        if pila:
            return pila.pop()
        return None

    # ===== UTILITARIOS =====

    @staticmethod
    def altura_arbol(nodo):
        if nodo is None:
            return 0
        return max(ArbolAVL.altura_arbol(nodo.get_izquierdo()),
                   ArbolAVL.altura_arbol(nodo.get_derecho())) + 1

    def peso(self, nodo):
        if nodo is None:
            return
        self.count += 1
        self.peso(nodo.get_izquierdo())
        self.peso(nodo.get_derecho())

    # ===== MÉTODOS PARA VISUALIZACIÓN EN JUEGO =====

    def inorden_texto(self, nodo, resultado):
        if nodo is None:
            return
        self.inorden_texto(nodo.get_izquierdo(), resultado)
        resultado.append("  [%d] %s" % (nodo.get_clave(), nodo.get_publicacion().contenido[:40]))
        self.inorden_texto(nodo.get_derecho(), resultado)

    def preorden_texto(self, nodo, resultado):
        if nodo is None:
            return
        resultado.append("  [%d] %s" % (nodo.get_clave(), nodo.get_publicacion().contenido[:40]))
        self.preorden_texto(nodo.get_izquierdo(), resultado)
        self.preorden_texto(nodo.get_derecho(), resultado)

    def posorden_texto(self, nodo, resultado):
        if nodo is None:
            return
        self.posorden_texto(nodo.get_izquierdo(), resultado)
        self.posorden_texto(nodo.get_derecho(), resultado)
        resultado.append("  [%d] %s" % (nodo.get_clave(), nodo.get_publicacion().contenido[:40]))

    def imprimir_texto(self, nodo, nivel, resultado):
        if nodo is not None:
            self.imprimir_texto(nodo.get_derecho(), nivel + 1, resultado)
            resultado.append("   " * nivel + str(nodo.get_clave()))
            self.imprimir_texto(nodo.get_izquierdo(), nivel + 1, resultado)
