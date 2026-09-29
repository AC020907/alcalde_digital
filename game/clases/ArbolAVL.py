from clases.NodoAVL import NodoAVL
from clases.Clase_pila import Clase_pila


class ArbolAVL:

    def __init__(self):
        self.raiz = None
        self.count = 0
        self.grado = 0

    def get_raiz(self):
        return self.raiz

    def set_raiz(self, r):
        self.raiz = r

    def agregar(self, publicacion):
        self.raiz = self.insertar(self.raiz, publicacion.nivel_riesgo, publicacion)

    # ===== MÉTODOS AVL =====

    def altura_nodo(self, nodo):
        if nodo is None:
            return 0
        return nodo.get_altura()

    def factor_equilibrio(self, nodo):
        if nodo is None:
            return 0
        return self.altura_nodo(nodo.get_izquierdo()) - self.altura_nodo(nodo.get_derecho())

    def rotacion_der(self, y):
        x = y.get_izquierdo()
        temporal = x.get_derecho()

        x.set_derecho(y)
        y.set_izquierdo(temporal)

        self._actualizar_altura(y)
        self._actualizar_altura(x)

        return x

    def rotacion_izq(self, y):
        x = y.get_derecho()
        temporal = x.get_izquierdo()

        x.set_izquierdo(y)
        y.set_derecho(temporal)

        self._actualizar_altura(y)
        self._actualizar_altura(x)

        return x

    def _actualizar_altura(self, nodo):
        nodo.set_altura(
            1 + max(
                self.altura_nodo(nodo.get_izquierdo()),
                self.altura_nodo(nodo.get_derecho())
            )
        )

    # ===== INSERCIÓN =====

    def insertar(self, nodo, clave, pub):
        if nodo is None:
            return NodoAVL(clave, pub)

        if clave < nodo.get_clave():
            nodo.set_izquierdo(self.insertar(nodo.get_izquierdo(), clave, pub))
        elif clave > nodo.get_clave():
            nodo.set_derecho(self.insertar(nodo.get_derecho(), clave, pub))
        else:
            return nodo  # clave duplicada: no se inserta

        self._actualizar_altura(nodo)
        balance = self.factor_equilibrio(nodo)

        # Rotacion simple derecha (LL)
        if balance > 1 and clave < nodo.get_izquierdo().get_clave():
            return self.rotacion_der(nodo)

        # Rotacion simple izquierda (RR)
        if balance < -1 and clave > nodo.get_derecho().get_clave():
            return self.rotacion_izq(nodo)

        # Rotacion doble izquierda-derecha (LR)
        if balance > 1 and clave > nodo.get_izquierdo().get_clave():
            nodo.set_izquierdo(self.rotacion_izq(nodo.get_izquierdo()))
            return self.rotacion_der(nodo)

        # Rotacion doble derecha-izquierda (RL)
        if balance < -1 and clave < nodo.get_derecho().get_clave():
            nodo.set_derecho(self.rotacion_der(nodo.get_derecho()))
            return self.rotacion_izq(nodo)

        return nodo

    # ===== BÚSQUEDA =====

    def buscar(self, nodo, clave):
        if nodo is None:
            return None

        if clave == nodo.get_clave():
            return nodo

        if clave < nodo.get_clave():
            return self.buscar(nodo.get_izquierdo(), clave)
        else:
            return self.buscar(nodo.get_derecho(), clave)

    # ===== ELIMINACIÓN =====

    def borrar(self, clave):
        self.raiz = self.eliminar(self.raiz, clave)

    def eliminar(self, nodo, clave):
        if nodo is None:
            return None

        if clave < nodo.get_clave():
            nodo.set_izquierdo(self.eliminar(nodo.get_izquierdo(), clave))
        elif clave > nodo.get_clave():
            nodo.set_derecho(self.eliminar(nodo.get_derecho(), clave))
        else:
            # Caso: nodo hoja o un solo hijo
            if nodo.get_izquierdo() is None:
                return nodo.get_derecho()
            elif nodo.get_derecho() is None:
                return nodo.get_izquierdo()

            # Caso: dos hijos — sucesor en inorden (minimo del subarbol derecho)
            sucesor = self.minimo_nodo(nodo.get_derecho())
            nodo.set_clave(sucesor.get_clave())
            nodo.set_publicacion(sucesor.get_publicacion())
            nodo.set_derecho(self.eliminar(nodo.get_derecho(), sucesor.get_clave()))

        self._actualizar_altura(nodo)
        balance = self.factor_equilibrio(nodo)

        if balance > 1 and self.factor_equilibrio(nodo.get_izquierdo()) >= 0:
            return self.rotacion_der(nodo)

        if balance > 1 and self.factor_equilibrio(nodo.get_izquierdo()) < 0:
            nodo.set_izquierdo(self.rotacion_izq(nodo.get_izquierdo()))
            return self.rotacion_der(nodo)

        if balance < -1 and self.factor_equilibrio(nodo.get_derecho()) <= 0:
            return self.rotacion_izq(nodo)

        if balance < -1 and self.factor_equilibrio(nodo.get_derecho()) > 0:
            nodo.set_derecho(self.rotacion_der(nodo.get_derecho()))
            return self.rotacion_izq(nodo)

        return nodo

    def minimo_nodo(self, nodo):
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

    def imprimir(self, nodo, nivel):
        if nodo is not None:
            self.imprimir(nodo.get_derecho(), nivel + 1)
            print("      " * nivel + str(nodo.get_clave()))
            self.imprimir(nodo.get_izquierdo(), nivel + 1)

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

    # ===== RECORRIDOS ITERATIVOS (lista como pila, igual que Stack de Java) =====

    def preorden_iterativo(self, nodo):
        pila = Clase_pila()
        p = nodo
        while p is not None or not pila.esta_vacia():
            if p is not None:
                print(str(p.get_clave()) + "-", end="")
                pila.impila(p)
                p = p.get_izquierdo()
            else:
                p = pila.campila()
                p = p.get_derecho()

    def inorden_iterativo(self, nodo):
        pila = Clase_pila()
        p = nodo
        while p is not None or not pila.esta_vacia():
            if p is not None:
                pila.impila(p)
                p = p.get_izquierdo()
            else:
                p = pila.campila()
                print(str(p.get_clave()) + "-", end="")
                p = p.get_derecho()

    def posorden_iterativo(self, nodo):
        if nodo is None:
            return
        pila1 = Clase_pila()
        pila2 = Clase_pila()
        pila1.impila(nodo)
        while not pila1.esta_vacia():
            p = pila1.campila()
            pila2.impila(p)
            if p.get_izquierdo() is not None:
                pila1.impila(p.get_izquierdo())
            if p.get_derecho() is not None:
                pila1.impila(p.get_derecho())
        while not pila2.esta_vacia():
            print(str(pila2.campila().get_clave()) + "-", end="")

    # ===== UTILITARIOS =====

    @staticmethod
    def altura_arbol(n1):
        if n1 is None:
            return 0
        return max(ArbolAVL.altura_arbol(n1.get_izquierdo()),
                   ArbolAVL.altura_arbol(n1.get_derecho())) + 1

    def peso(self, nodo):
        if nodo is None:
            return
        self.count += 1
        self.peso(nodo.get_izquierdo())
        self.peso(nodo.get_derecho())

    def hojas(self, nodo):
        if nodo is None:
            return
        if nodo.get_izquierdo() is None and nodo.get_derecho() is None:
            self.count += 1
        self.hojas(nodo.get_izquierdo())
        self.hojas(nodo.get_derecho())

    def gradoArbol(self, nodo):
        if nodo is None:
            return
        hijos = 0
        if nodo.get_izquierdo() is not None:
            hijos += 1
        if nodo.get_derecho() is not None:
            hijos += 1
        if hijos > self.grado:
            self.grado = hijos
        self.gradoArbol(nodo.get_izquierdo())
        self.gradoArbol(nodo.get_derecho())

    def suma(self, nodo):
        if nodo is None:
            return 0
        return nodo.get_clave() + self.suma(nodo.get_izquierdo()) + self.suma(nodo.get_derecho())

    def esPerfecto(self, nodo):
        self.count = 0
        self.peso(nodo)
        altura = ArbolAVL.altura_arbol(nodo)
        nodos_esperados = (2 ** altura) - 1
        return self.count == nodos_esperados

    def nodosEnNivel(self, nodo, nivel):
        if nodo is None or nivel < 0:
            return 0
        cola = [nodo]
        nivel_actual = 0
        while cola:
            cantidad = len(cola)
            if nivel_actual == nivel:
                return cantidad
            siguiente = []
            for actual in cola:
                if actual.get_izquierdo() is not None:
                    siguiente.append(actual.get_izquierdo())
                if actual.get_derecho() is not None:
                    siguiente.append(actual.get_derecho())
            cola = siguiente
            nivel_actual += 1
        return 0

    def buscarPadre(self, nodo_actual, objetivo):
        if nodo_actual is None:
            return None
        izq = nodo_actual.get_izquierdo()
        der = nodo_actual.get_derecho()
        if (izq is not None and izq.get_clave() == objetivo) or \
           (der is not None and der.get_clave() == objetivo):
            return nodo_actual
        resultado = self.buscarPadre(izq, objetivo)
        if resultado is not None:
            return resultado
        return self.buscarPadre(der, objetivo)

    def tio(self, nodo, valor):
        if nodo is None:
            return -1
        padre = self.buscarPadre(self.raiz, nodo.get_clave())
        if padre is None:
            return -1
        abuelo = self.buscarPadre(self.raiz, padre.get_clave())
        if abuelo is None:
            return -1
        if abuelo.get_izquierdo() == padre:
            if abuelo.get_derecho() is not None:
                return abuelo.get_derecho().get_clave()
        else:
            if abuelo.get_izquierdo() is not None:
                return abuelo.get_izquierdo().get_clave()
        return -1

    # ===== MÉTODOS PARA VISUALIZACIÓN EN JUEGO =====

    def preorden_texto(self, nodo, resultado):
        if nodo is None:
            return
        resultado.append(f"  Riesgo {nodo.get_clave()}: {nodo.get_publicacion().contenido}")
        self.preorden_texto(nodo.get_izquierdo(), resultado)
        self.preorden_texto(nodo.get_derecho(), resultado)

    def inorden_texto(self, nodo, resultado):
        if nodo is None:
            return
        self.inorden_texto(nodo.get_izquierdo(), resultado)
        resultado.append(f"  Riesgo {nodo.get_clave()}: {nodo.get_publicacion().contenido}")
        self.inorden_texto(nodo.get_derecho(), resultado)

    def posorden_texto(self, nodo, resultado):
        if nodo is None:
            return
        self.posorden_texto(nodo.get_izquierdo(), resultado)
        self.posorden_texto(nodo.get_derecho(), resultado)
        resultado.append(f"  Riesgo {nodo.get_clave()}: {nodo.get_publicacion().contenido}")

    def imprimir_texto(self, nodo, nivel, resultado):
        if nodo is not None:
            self.imprimir_texto(nodo.get_derecho(), nivel + 1, resultado)
            resultado.append("   " * nivel + str(nodo.get_clave()))
            self.imprimir_texto(nodo.get_izquierdo(), nivel + 1, resultado)
