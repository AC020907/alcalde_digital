class NodoDecision:
    def __init__(self, texto, consecuencia=None, etiqueta=None):
        self.texto = texto
        self.consecuencia = consecuencia
        self.etiqueta = etiqueta
        self.hijos = []

    def agregar_hijo(self, nodo):
        self.hijos.append(nodo)

    def es_hoja(self):
        return len(self.hijos) == 0
