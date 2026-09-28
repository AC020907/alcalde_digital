class NodoAVL:

    def __init__(self, clave, publicacion):
        self.clave = clave
        self.publicacion = publicacion
        self.izquierdo = None
        self.derecho = None
        self.altura = 1

    def get_clave(self):
        return self.clave

    def set_clave(self, c):
        self.clave = c

    def get_publicacion(self):
        return self.publicacion

    def set_publicacion(self, p):
        self.publicacion = p

    def get_izquierdo(self):
        return self.izquierdo

    def set_izquierdo(self, n):
        self.izquierdo = n

    def get_derecho(self):
        return self.derecho

    def set_derecho(self, n):
        self.derecho = n

    def get_altura(self):
        return self.altura

    def set_altura(self, h):
        self.altura = h
