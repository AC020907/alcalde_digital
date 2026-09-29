class Clase_pila:

    def __init__(self):
        self._pila = []

    def impila(self, elemento):
        self._pila.append(elemento)

    def campila(self):
        if not self._pila:
            return None
        return self._pila.pop()

    def peek(self):
        if not self._pila:
            return None
        return self._pila[-1]

    def esta_vacia(self):
        return len(self._pila) == 0

    def tamanio(self):
        return len(self._pila)
