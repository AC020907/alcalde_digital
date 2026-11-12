class NodoDecision:
    def __init__(self, texto, consecuencia=None, etiqueta=None):
        self.texto = texto
        self.consecuencia = consecuencia
        self.etiqueta = etiqueta
        self.hijos = []
        self.padre = None

    def agregar_hijo(self, nodo):
        nodo.padre = self
        self.hijos.append(nodo)

    def quitar_hijo(self, nodo):
        self.hijos.remove(nodo)
        nodo.padre = None

    def es_hoja(self):
        return len(self.hijos) == 0
