"""Escrutinio del modo Historia: cuatro candidatos, coherente con cada final y sensible a los indicadores."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from clases.Eleccion import escrutinio_historia, ELECTORES  # noqa: E402

BUENA = {"info_verificada": 80, "confianza": 75, "convivencia": 70, "bienestar": 70, "desinformacion": 20, "conflictos": 15}
MALA = {"info_verificada": 25, "confianza": 25, "convivencia": 30, "bienestar": 30, "desinformacion": 80, "conflictos": 75}


class TestEscrutinio(unittest.TestCase):
    def test_cuatro_candidatos_y_totales(self):
        for final in ("informada", "dividida", "caos", "mandato", "secreto"):
            e = escrutinio_historia(final, BUENA, 60, semilla=3)
            self.assertEqual(len(e["candidatos"]), 4)
            self.assertAlmostEqual(sum(c["votos"] for c in e["candidatos"]), e["votantes"], delta=4)
            self.assertEqual(e["votantes"] + e["abstencion"], ELECTORES)
            self.assertTrue(e["explicacion"])

    def test_coherente_con_cada_final(self):
        self.assertEqual(escrutinio_historia("mandato", MALA, 30)["ganador"], "alcalde")
        caos = escrutinio_historia("caos", MALA, 30)
        self.assertTrue(caos["impugnado"])
        self.assertIsNone(caos["ganador"])
        d = escrutinio_historia("dividida", BUENA, 50)
        votos = {c["id"]: c["votos"] for c in d["candidatos"]}
        self.assertEqual(abs(votos["alcalde"] - votos["vega"]), 4000)

    def test_las_decisiones_cambian_participacion_y_ganador(self):
        buena = escrutinio_historia("informada", BUENA, 85)
        mala = escrutinio_historia("informada", MALA, 20)
        self.assertGreater(buena["participacion"], mala["participacion"])
        self.assertEqual(buena["ganador"], "alcalde")
        self.assertNotEqual(mala["ganador"], "alcalde")

    def test_reproducible(self):
        self.assertEqual(escrutinio_historia("informada", BUENA, 60, 9), escrutinio_historia("informada", BUENA, 60, 9))


if __name__ == "__main__":
    unittest.main()
