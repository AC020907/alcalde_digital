"""Coherencia educativa: ninguna accion irresponsable se recompensa, en Historia ni en Arena (rubrica §2, §11)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from clases.Publicacion import armar_publicacion  # noqa: E402
from clases.publicaciones_historia import PUBLICACIONES_HISTORIA  # noqa: E402
from clases.arena import reglas as R  # noqa: E402


def puntos(rama):
    return rama["efecto"].get("puntos", 0)


class TestHistoria(unittest.TestCase):
    def test_hay_verdaderas_y_falsas(self):
        tipos = {p["es_falsa"] for p in PUBLICACIONES_HISTORIA}
        self.assertEqual(tipos, {True, False})

    def test_compartir_falsa_sin_verificar_es_negativo(self):
        for p in PUBLICACIONES_HISTORIA:
            if p["es_falsa"]:
                e = p["compartir"]["efecto"]
                self.assertLess(puntos(p["compartir"]), 0, p["contenido"])
                self.assertGreater(e.get("desinformacion", 0), 0, p["contenido"])

    def test_verificar_bien_lo_verdadero_beneficia_y_es_lo_mejor(self):
        for p in PUBLICACIONES_HISTORIA:
            if not p["es_falsa"]:
                self.assertGreater(puntos(p["verificar_si"]), 0, p["contenido"])
                self.assertGreater(puntos(p["verificar_si"]), puntos(p["compartir"]), p["contenido"])

    def test_reportar_lo_verdadero_tiene_coste(self):
        for p in PUBLICACIONES_HISTORIA:
            if not p["es_falsa"]:
                self.assertLess(puntos(p["verificar_no"]), 0, p["contenido"])
                self.assertLessEqual(p["verificar_no"]["efecto"].get("confianza", 0), 0, p["contenido"])

    def test_avalar_lo_falso_tiene_coste_y_desmentirlo_beneficia(self):
        for p in PUBLICACIONES_HISTORIA:
            if p["es_falsa"]:
                self.assertLess(puntos(p["verificar_si"]), 0, p["contenido"])
                self.assertGreater(p["verificar_si"]["efecto"].get("desinformacion", 0), 0, p["contenido"])
                self.assertGreater(puntos(p["verificar_no"]), 0, p["contenido"])
                self.assertLess(p["verificar_no"]["efecto"].get("desinformacion", 0), 0, p["contenido"])

    def test_ignorar_nunca_da_puntos(self):
        for p in PUBLICACIONES_HISTORIA:
            self.assertLessEqual(puntos(p["ignorar"]), 0, p["contenido"])

    def test_la_mejor_accion_coincide_con_la_verdad(self):
        for p in PUBLICACIONES_HISTORIA:
            ramas = {k: puntos(p[k]) for k in ("compartir", "ignorar", "verificar_si", "verificar_no")}
            mejor = max(ramas, key=ramas.get)
            self.assertEqual(mejor, "verificar_no" if p["es_falsa"] else "verificar_si", p["contenido"])

    def test_cada_publicacion_muestra_una_pista_al_verificar(self):
        for p in PUBLICACIONES_HISTORIA:
            pub = armar_publicacion(**p)
            verificar = pub.arbol.raiz.hijos[1]
            self.assertIn(p["pista"], verificar.texto)
            self.assertEqual(len(verificar.hijos), 2)


class TestArena(unittest.TestCase):
    def setUp(self):
        p = R.Partida()
        p.unir("a", "A", "ciudadano")
        self.j = p.jugadores["a"]
        self.p = p

    def valor(self, accion, tipo):
        return self.p._valorar(self.j, accion, tipo, R.POR_ID["agua"])[0]

    def test_compartir_falsa_negativo_y_verificar_verdad_positivo(self):
        self.assertLess(self.valor(R.COMPARTIR, "falsa"), 0)
        self.assertLess(self.valor(R.VERIFICADA, "falsa"), self.valor(R.COMPARTIR, "falsa"))
        self.assertGreater(self.valor(R.VERIFICADA, "verdadera"), self.valor(R.COMPARTIR, "verdadera"))

    def test_reportar_verdad_tiene_coste(self):
        self.assertLess(self.valor(R.REPORTAR, "verdadera"), 0)
        self.assertLess(self.valor(R.REPORTAR_FALSA, "verdadera"), 0)

    def test_una_opinion_no_es_desinformacion(self):
        self.assertLess(self.valor(R.REPORTAR_FALSA, "opinion"), 0)
        self.assertGreater(self.valor(R.IGNORAR, "opinion"), 0)
        self.assertGreater(self.valor(R.VERIFICADA, "opinion"), 0)

    def test_misma_regla_en_ambos_modos(self):
        """En los dos modos, desmentir lo falso y verificar lo verdadero son la mejor accion."""
        for tipo, mejor in (("falsa", R.REPORTAR_FALSA), ("verdadera", R.VERIFICADA)):
            valores = {a: self.valor(a, tipo) for a in (R.COMPARTIR, R.VERIFICADA, R.IGNORAR, R.REPORTAR, R.REPORTAR_FALSA)}
            self.assertEqual(max(valores, key=valores.get), mejor)


if __name__ == "__main__":
    unittest.main()
