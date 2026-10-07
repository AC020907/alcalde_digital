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
        return [(h.etiqueta, i) for i, h in enumerate(self.actual.hijos)]

    def elegir(self, indice):
        self.actual = self.publicacion.arbol.avanzar(self.actual, indice)
        return self.actual

    def terminada(self):
        return self.actual.es_hoja()

    def en_verificacion(self):
        """True si el nodo actual es el de '?Es verdadera?' (dos hijos: Si / No)."""
        return self.actual is not self.publicacion.arbol.raiz and len(self.actual.hijos) == 2

    def resolver_verificacion(self):
        """Verificar revela la verdad: avanza a la hoja Si (verdadera) o No (falsa)."""
        indice = 1 if self.publicacion.es_falsa else 0
        return self.elegir(indice)


class BancoPublicaciones:

    def __init__(self, publicaciones):
        self.avl = ArbolAVL()
        for pub in publicaciones:
            self.avl.agregar(pub)

    def hay_mas(self):
        return self.avl.raiz is not None

    def siguiente(self):
        nodo = self.avl.minimo_nodo(self.avl.raiz)
        self.avl.borrar(nodo.get_clave())
        return nodo.get_publicacion()

    def inorden_riesgos(self):
        resultado = []
        self.avl.inorden_texto(self.avl.raiz, resultado)
        return resultado


def armar_publicacion(autor, contenido, es_falsa, nivel_riesgo,
                      compartir, ignorar, verificar_si, verificar_no):
    """
    Construye el arbol de decisiones del PDF (pag. 4):

        ¿Que quieres hacer?
        ├─[0] Compartir         → hoja
        ├─[1] Verificar
        │     └─ ¿Es verdadera?
        │         ├─[0] Si → Compartir  → hoja
        │         └─[1] No → Reportar   → hoja
        └─[2] Ignorar           → hoja

    Cada accion es un dict con claves: etiqueta, texto, efecto
    """
    arbol = ArbolDecisiones()
    raiz = arbol.insertar_raiz("?Que quieres hacer?")

    # Rama 0 — Compartir directamente
    arbol.insertar_hijo(raiz,
                        compartir["texto"],
                        compartir.get("efecto"),
                        compartir["etiqueta"])

    # Rama 1 — Verificar (nodo intermedio)
    nodo_verificar = arbol.insertar_hijo(raiz,
                                         "?Es verdadera la publicacion?",
                                         None,
                                         "Verificar antes de actuar")

    arbol.insertar_hijo(nodo_verificar,
                        verificar_si["texto"],
                        verificar_si.get("efecto"),
                        verificar_si["etiqueta"])

    arbol.insertar_hijo(nodo_verificar,
                        verificar_no["texto"],
                        verificar_no.get("efecto"),
                        verificar_no["etiqueta"])

    # Rama 2 — Ignorar
    arbol.insertar_hijo(raiz,
                        ignorar["texto"],
                        ignorar.get("efecto"),
                        ignorar["etiqueta"])

    return Publicacion(autor, contenido, es_falsa, nivel_riesgo, arbol)
