"""Apertura de la Feria Gamer (game/story/apertura.rpy y prologo.rpy): reglas que no deben romperse."""
import os
import re
import sys
import unittest

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "game"))
sys.path.insert(0, RAIZ)

from clases.RedCivitas import crear_red_civitas  # noqa: E402
from clases.moderacion_datos import COMENTARIOS_MODERACION  # noqa: E402


def leer(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as f:
        return f.read()


APERTURA = leer("story/apertura.rpy")
PROLOGO = leer("story/prologo.rpy")


def propagar(eleccion):
    """Mismos parametros que apertura_propagacion()."""
    red = crear_red_civitas()
    if eleccion == "desmentir":
        bloqueados, factor = set(red.vecinos("jugador")), 1.0
    elif eleccion == "analisis":
        bloqueados, factor = {"@salud.nova", "@investigador.nova", "@noticias.nova"}, 1.0
    else:
        bloqueados, factor = set(), 1.35
    niveles = red.bfs_propagacion("@verdad.oculta", semilla="apertura", factor=factor, bloqueados=bloqueados)
    return sum(len(n) for n in niveles) - 1, niveles


class Apertura(unittest.TestCase):
    def test_los_parametros_del_test_son_los_del_juego(self):
        self.assertIn('APERTURA_SEMILLA = "apertura"', APERTURA)
        self.assertIn('bloqueados, factor = set(red.vecinos("jugador")), 1.0', APERTURA)
        self.assertIn('bloqueados, factor = set(APERTURA_MEDIOS), 1.0', APERTURA)
        self.assertIn('bloqueados, factor = set(), 1.35', APERTURA)

    def test_no_intervenir_deja_correr_mas_el_rumor(self):
        alcance = {e: propagar(e)[0] for e in ("desmentir", "analisis", "ignorar")}
        self.assertGreater(alcance["ignorar"], alcance["analisis"])
        self.assertGreater(alcance["ignorar"], alcance["desmentir"])
        # Pedir analisis no frena el rumor de inmediato: sigue corriendo casi como con el desmentido.
        self.assertGreaterEqual(alcance["analisis"], alcance["desmentir"] - 2)

    def test_la_propagacion_es_reproducible_y_parte_de_la_cuenta_falsa(self):
        a, niv_a = propagar("ignorar")
        b, niv_b = propagar("ignorar")
        self.assertEqual(niv_a, niv_b)
        self.assertEqual(niv_a[0], ["@verdad.oculta"])

    def test_se_conservan_las_consecuencias_del_prologo_original(self):
        self.assertIn('{"confianza": 2, "info_verificada": -2}', APERTURA)      # desmentir sin datos
        self.assertIn('{"info_verificada": 3, "desinformacion": 2}', APERTURA)  # pedir analisis
        self.assertIn('{"desinformacion": 4, "confianza": -2}', APERTURA)       # ignorar
        for marca in ("desmintio_sin_datos", "pidio_analisis", "ignoro_rumor_agua", "prologo_agua"):
            self.assertIn(marca, APERTURA)
        self.assertIn('dar_pista("hip_nova_creo")', PROLOGO)
        self.assertIn('estilo_alcalde = "Analítico"', PROLOGO)

    def test_la_decision_se_aplica_una_sola_vez(self):
        cuerpo = APERTURA.split("def apertura_decidir")[1].split("def ")[0]
        self.assertIn("if store.apertura_decision is not None:", cuerpo)
        self.assertEqual(PROLOGO.count("apertura_decidir("), 1)
        self.assertEqual(PROLOGO.count("aplicar_consecuencia"), 0)

    def test_microprueba_no_repite_comentarios_del_reto_completo(self):
        autores_apertura = set(re.findall(r'\("(@[\w.]+)", "[^"]+", (?:True|False)\)', APERTURA))
        self.assertEqual(len(autores_apertura), 4)
        autores_banco = {a for a, _t, _c, _b in COMENTARIOS_MODERACION}
        self.assertFalse(autores_apertura & autores_banco)

    def test_microprueba_no_toca_el_registro_del_moderador(self):
        micro = APERTURA.split("label apertura_microprueba")[1]
        self.assertNotIn("registrar_minijuego", micro)
        self.assertIn("ColaModeracion(", micro)
        self.assertIn("moderador_ui", micro)

    def test_las_opciones_del_menu_coinciden_con_los_perfiles_de_qa(self):
        for opcion in ("Publicar un desmentido", "Pedir los análisis", "No intervenir"):
            self.assertIn(opcion, PROLOGO)
        self.assertIn('"No intervenir"', leer("qa_autoplay.rpy"))


if __name__ == "__main__":
    unittest.main()
