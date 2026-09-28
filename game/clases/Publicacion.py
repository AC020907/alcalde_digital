import random
from clases.Tree import ArbolDecisiones
from clases.ArbolAVL import ArbolAVL


class Publicacion:

    def __init__(self, autor, contenido, es_falsa, nivel_riesgo, arbol):
        self.autor = autor
        self.contenido = contenido
        self.es_falsa = es_falsa
        self.nivel_riesgo = nivel_riesgo
        self.arbol = arbol


class SesionPublicacion:

    def __init__(self, publicacion):
        self.publicacion = publicacion
        self.actual = publicacion.arbol.raiz

    def opciones(self):
        ops = []
        if self.actual.izquierda:
            ops.append((self.actual.izquierda.etiqueta, 'izq'))
        if self.actual.derecha:
            ops.append((self.actual.derecha.etiqueta, 'der'))
        return ops

    def elegir(self, eleccion):
        self.actual = self.publicacion.arbol.avanzar(self.actual, eleccion)
        return self.actual

    def terminada(self):
        return self.actual.es_hoja()


class BancoPublicaciones:

    def __init__(self, publicaciones):
        self.avl = ArbolAVL()
        for pub in publicaciones:
            self.avl.agregar(pub)

    def hay_mas(self):
        return self.avl.raiz is not None

    def siguiente(self):
        # Entrega la publicacion de MENOR riesgo primero: escalada progresiva
        nodo = self.avl._minimo_nodo(self.avl.raiz)
        self.avl.borrar(nodo.get_clave())
        return nodo.get_publicacion()

    def inorden_riesgos(self):
        resultado = []
        self.avl.inorden_texto(self.avl.raiz, resultado)
        return resultado


def armar_publicacion(autor, contenido, es_falsa, nivel_riesgo, pregunta, izq, der):
    arbol = ArbolDecisiones()
    arbol.insertar(pregunta, [])
    arbol.insertar(izq["texto"], ['izq'], izq.get("efecto"), izq["etiqueta"])
    arbol.insertar(der["texto"], ['der'], der.get("efecto"), der["etiqueta"])
    return Publicacion(autor, contenido, es_falsa, nivel_riesgo, arbol)
