"""AVL del banco de publicaciones (rubrica §5): insercion, eliminacion, busqueda, recorridos y balanceo."""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from clases.ArbolAVL import ArbolAVL  # noqa: E402
from clases.Publicacion import BancoPublicaciones, armar_publicacion  # noqa: E402
from clases.publicaciones_historia import PUBLICACIONES_HISTORIA  # noqa: E402


class Pub(object):
    def __init__(self, riesgo):
        self.nivel_riesgo = riesgo


def claves_inorden(avl):
    res = []

    def ir(n):
        if n is None:
            return
        ir(n.get_izquierdo())
        res.append(n.get_clave())
        ir(n.get_derecho())
    ir(avl.raiz)
    return res


def verificar_avl(test, avl, n):
    def altura(n):
        if n is None:
            return 0
        hi, hd = altura(n.get_izquierdo()), altura(n.get_derecho())
        test.assertLessEqual(abs(hi - hd), 1, "desbalanceado en %s" % n.get_clave())
        return 1 + max(hi, hd)
    altura(n)


class TestAVL(unittest.TestCase):
    def test_insercion_ordenada_queda_balanceada(self):
        avl = ArbolAVL()
        for k in range(1, 101):          # el peor caso para un ABB sin balanceo
            avl.agregar(Pub(k))
        verificar_avl(self, avl, avl.raiz)
        self.assertEqual(claves_inorden(avl), list(range(1, 101)))
        self.assertLessEqual(avl.altura_nodo(avl.raiz), 8)   # 1.44 log2(100) ~ 9.6; AVL real ~7-8

    def test_insercion_y_eliminacion_aleatorias(self):
        rng = random.Random(3)
        claves = rng.sample(range(1000), 200)
        avl = ArbolAVL()
        for k in claves:
            avl.agregar(Pub(k))
        for k in claves[:120]:
            avl.borrar(k)
            verificar_avl(self, avl, avl.raiz)
        self.assertEqual(claves_inorden(avl), sorted(claves[120:]))

    def test_busqueda_y_extremos(self):
        avl = ArbolAVL()
        for k in (50, 20, 80, 10, 30):
            avl.agregar(Pub(k))
        self.assertIsNotNone(avl.buscar(avl.raiz, 30))
        self.assertIsNone(avl.buscar(avl.raiz, 31))
        self.assertEqual(avl.minimo_nodo(avl.raiz).get_clave(), 10)
        self.assertEqual(avl.maximo_nodo(avl.raiz).get_clave(), 80)

    def test_banco_entrega_de_menor_a_mayor_riesgo(self):
        banco = BancoPublicaciones([armar_publicacion(**p) for p in PUBLICACIONES_HISTORIA])
        riesgos = []
        while banco.hay_mas():
            riesgos.append(banco.siguiente().nivel_riesgo)
        self.assertEqual(riesgos, sorted(p["nivel_riesgo"] for p in PUBLICACIONES_HISTORIA))
        self.assertFalse(banco.hay_mas())


if __name__ == "__main__":
    unittest.main()
