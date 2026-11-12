"""Finales (clases/Destinos.py) y Puntuacion Civica (clases/Puntuacion.py): logica pura."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from clases import Destinos as D  # noqa: E402
from clases import Puntuacion as P  # noqa: E402
from clases import Investigacion as inv  # noqa: E402


def estado(**cambios):
    base = {"forzado": None, "derrota": False, "secreto_publicado": False, "secreto_disponible": False,
            "uso_audio": False, "viral_ok": True, "desinformacion": 40, "confianza": 60, "reputacion": 60,
            "salud_ciudad": 60}
    base.update(cambios)
    return base


CIUDAD_SANA = dict(info_verificada=70, confianza=70, convivencia=70, bienestar=70, desinformacion=25, conflictos=20)
CIUDAD_ROTA = dict(info_verificada=30, confianza=30, convivencia=40, bienestar=40, desinformacion=75, conflictos=70)


class Finales(unittest.TestCase):
    def test_cada_final_es_alcanzable(self):
        casos = {
            D.INFORMADA: estado(),
            D.DIVIDIDA: estado(viral_ok=False, confianza=60, desinformacion=30),
            D.CAOS: estado(desinformacion=70),
            D.MANDATO: estado(uso_audio=True),
            D.SECRETO: estado(secreto_publicado=True, secreto_disponible=True),
        }
        for final, est in casos.items():
            self.assertEqual(D.decidir_final(est), final, final)
        self.assertEqual(set(casos), set(D.FINALES))

    def test_derrota_y_forzado_mandan(self):
        self.assertEqual(D.decidir_final(estado(derrota=True, secreto_publicado=True, secreto_disponible=True)), D.CAOS)
        self.assertEqual(D.decidir_final(estado(forzado=D.DIVIDIDA)), D.DIVIDIDA)

    def test_no_se_destapa_lo_que_usaste(self):
        est = estado(secreto_publicado=True, secreto_disponible=True, uso_audio=True)
        self.assertEqual(D.decidir_final(est), D.MANDATO)

    def test_secreto_exige_evidencia_y_publicacion(self):
        self.assertNotEqual(D.decidir_final(estado(secreto_publicado=True)), D.SECRETO)
        self.assertNotEqual(D.decidir_final(estado(secreto_disponible=True)), D.SECRETO)

    def test_colapso_pesa_mas_que_el_mandato(self):
        self.assertEqual(D.decidir_final(estado(uso_audio=True, desinformacion=80)), D.CAOS)

    def test_perder_el_climax_con_ciudad_debil_es_caos(self):
        self.assertEqual(D.decidir_final(estado(viral_ok=False, confianza=45, desinformacion=40)), D.CAOS)
        self.assertEqual(D.decidir_final(estado(viral_ok=False, confianza=60, desinformacion=55)), D.CAOS)
        self.assertEqual(D.decidir_final(estado(viral_ok=False, confianza=65, desinformacion=30)), D.DIVIDIDA)

    def test_alcalde_que_difunde_falsedades_no_logra_ciudad_informada(self):
        self.assertEqual(D.decidir_final(estado(falsas_compartidas=2)), D.DIVIDIDA)
        self.assertEqual(D.decidir_final(estado(falsas_compartidas=1)), D.INFORMADA)

    def test_informada_exige_ciudad_sana(self):
        self.assertEqual(D.decidir_final(estado(salud_ciudad=45)), D.DIVIDIDA)

    def test_catalogo_completo(self):
        for f in D.FINALES:
            for clave in ("titulo", "insignia", "color", "descripcion", "misterio"):
                self.assertTrue(D.DESTINOS[f][clave], (f, clave))


class Puntuacion(unittest.TestCase):
    def _total(self, final=None, **kw):
        args = dict(decisiones_pub=[], calidades={}, registro={}, pistas=[], grupos_clave=inv.PISTAS_CLAVE,
                    indicadores=CIUDAD_SANA, final=final)
        args.update(kw)
        return P.calcular(**args)

    def test_maximos_suman_mil(self):
        self.assertEqual(P.TOTAL_MAXIMO, 1000)

    def test_cotas_y_suma(self):
        perfecto = self._total(
            decisiones_pub=[(90, True, "verificar_no"), (10, False, "verificar_si")],
            calidades={"a": 1.0, "b": 1.0},
            registro={m: {"exito": True, "calificacion": "S"} for m in P.MINIJUEGOS},
            pistas=list(inv.PISTAS), indicadores=dict(info_verificada=100, confianza=100, convivencia=100,
                                                      bienestar=100, desinformacion=0, conflictos=0))
        self.assertEqual(perfecto["total"], 1000)
        for clave, maximo in P.MAXIMOS.items():
            self.assertLessEqual(perfecto[clave], maximo)
        self.assertEqual(perfecto["total"], sum(perfecto[c] for c in P.MAXIMOS))

    def test_vacio_no_rompe(self):
        r = self._total()
        self.assertGreaterEqual(r["total"], 0)
        self.assertEqual(r["verificacion"], 0)

    def test_compartir_falsa_castiga_mas_que_ignorar(self):
        compartir = P.puntos_verificacion([(80, True, "compartir")])
        ignorar = P.puntos_verificacion([(80, True, "ignorar")])
        verificar = P.puntos_verificacion([(80, True, "verificar_no")])
        self.assertLess(compartir, ignorar)
        self.assertLess(ignorar, verificar)

    def test_riesgo_pesa_mas(self):
        alto_bien = P.puntos_verificacion([(90, True, "verificar_no"), (10, True, "compartir")])
        bajo_bien = P.puntos_verificacion([(90, True, "compartir"), (10, True, "verificar_no")])
        self.assertGreater(alto_bien, bajo_bien)

    def test_caos_limita_ciudad(self):
        self.assertLessEqual(self._total(final="caos")["ciudad"], 50)

    def test_final_no_garantiza_maximo(self):
        r = self._total(final="secreto", pistas=["panel_programacion", "anuncio_resonancia", "testimonio_acueducto"])
        self.assertLess(r["total"], 1000)

    def test_minijuego_fallido_vale_poco_y_no_jugado_nada(self):
        self.assertEqual(P.puntos_minijuegos({}), 0)
        fallido = P.puntos_minijuegos({"moderador": {"exito": False}})
        bueno = P.puntos_minijuegos({"moderador": {"exito": True, "calificacion": "A"}})
        self.assertLess(0, fallido)
        self.assertLess(fallido, bueno)

    def test_investigacion_secreto_minimo_cumple_regla_del_servidor(self):
        # Camino mas corto al final secreto (feria): las tres pistas clave mas las que la historia da siempre.
        pistas = ["panel_programacion", "anuncio_resonancia", "testimonio_acueducto",
                  "hip_nova_creo", "giro_amplificacion", "audio_tomas", "conclusion_resonancia"]
        self.assertGreaterEqual(P.puntos_investigacion(pistas, inv.PISTAS_CLAVE), 100)
        self.assertEqual(sum(inv.grupos_clave({"pistas": {p: "x" for p in pistas}}).values()), 3)

    def test_ciudad_sana_y_rota(self):
        self.assertGreaterEqual(P.puntos_ciudad(**CIUDAD_SANA), 50)
        self.assertLess(P.puntos_ciudad(**CIUDAD_ROTA), 50)


if __name__ == "__main__":
    unittest.main()
