"""
Pruebas de logica pura (sin Ren'Py): catalogos, CivitasNet, expediente, eventos
variables, condiciones del final secreto y el puzzle del Rastreador.

Ejecutar desde la raiz del repositorio:
    python tests/test_civitas_logica.py
"""
import os
import pickle
import re
import sys
import unittest

JUEGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")
sys.path.insert(0, JUEGO)

from clases import Investigacion as inv  # noqa: E402
from clases.PuzzleEvidencias import PuzzleEvidencias  # noqa: E402
from clases.RedCivitas import crear_red_civitas  # noqa: E402

# Pistas que entrega la historia o un minijuego (no una publicacion de CivitasNet).
PISTAS_NARRATIVAS = {"hip_nova_creo", "intervalo_7min", "testimonio_acueducto", "filtracion_parcial",
                     "panel_programacion", "captura_recortada", "rectificacion_salud", "giro_amplificacion",
                     "nova_evade", "conclusion_resonancia"}


def estado(momento=0, hechos=(), pistas=(), eventos=None):
    return {"momento": momento, "hechos": list(hechos),
            "hechos_momento": {h: momento for h in hechos},
            "pistas": {p: inv.PISTAS[p]["estado"] for p in pistas},
            "pistas_nuevas": [], "posts_vistos": [], "eventos": eventos or {}, "semilla": 1}


def leer_rpy():
    for raiz, _, archivos in os.walk(JUEGO):
        for nombre in archivos:
            if nombre.endswith(".rpy") and not nombre.startswith("zz_"):
                with open(os.path.join(raiz, nombre), encoding="utf-8-sig") as f:
                    yield f.read()


def tokens(condicion):
    return [t.lstrip("!") for t in condicion]


class Catalogos(unittest.TestCase):

    def test_ids_unicos(self):
        ids = [p["id"] for p in inv.PUBLICACIONES_NET]
        self.assertEqual(len(ids), len(set(ids)))

    def test_referencias_validas(self):
        for post in inv.PUBLICACIONES_NET:
            if post["pista"]:
                self.assertIn(post["pista"], inv.PISTAS, post["id"])
            condiciones = list(post["condicion"]) + [t for c, _ in post["revelado"] for t in c]
            for t in tokens(condiciones):
                if t.startswith("pista:"):
                    self.assertIn(t[6:], inv.PISTAS, post["id"])
                elif t.startswith("evento:"):
                    self.assertIn(t[7:], inv.EVENTOS, post["id"])
                else:
                    self.assertIn(t, inv.HECHOS, post["id"])
            for _, nuevo_estado in post["revelado"]:
                self.assertIn(nuevo_estado, inv.ESTADOS_POST)
            if post["momento"] is None:
                self.assertTrue(post["condicion"], post["id"])

    def test_pistas_relaciones_y_estados(self):
        for pid, ficha in inv.PISTAS.items():
            self.assertIn(ficha["categoria"], inv.CATEGORIAS_PISTA)
            self.assertIn(ficha["estado"], inv.ESTADOS_PISTA)
            for r in ficha["relacion"]:
                self.assertIn(r, inv.PISTAS, pid)
            for e in ficha["por_estado"]:
                self.assertIn(e, inv.ESTADOS_PISTA)

    def test_toda_pista_tiene_una_fuente(self):
        en_posts = {p["pista"] for p in inv.PUBLICACIONES_NET if p["pista"]}
        for pid in inv.PISTAS:
            self.assertTrue(pid in en_posts or pid in PISTAS_NARRATIVAS, pid)

    def test_hechos_usados_en_rpy_existen(self):
        usados = set()
        for texto in leer_rpy():
            usados |= set(re.findall(r'\b(?:hecho|hay)\("([a-z_0-9]+)"\)', texto))
        self.assertTrue(usados)
        self.assertEqual(usados - set(inv.HECHOS), set())

    def test_pistas_usadas_en_rpy_existen(self):
        usadas = set()
        for texto in leer_rpy():
            usadas |= set(re.findall(r'(?:dar_pista|tiene_pista)\("([a-z_0-9]+)"', texto))
        self.assertEqual(usadas - set(inv.PISTAS), set())


class CivitasNet(unittest.TestCase):

    def test_feed_respeta_el_momento(self):
        for momento in range(5):
            for post in inv.feed_visible(estado(momento)):
                self.assertLessEqual(post["momento"], momento)

    def test_feed_sin_duplicados_y_ordenado(self):
        est = estado(4, hechos=inv.HECHOS, eventos={1: "cuenta_secundaria", 2: "testimonio_verificable"})
        feed = inv.feed_visible(est)
        self.assertEqual(len(feed), len({p["id"] for p in feed}))
        claves = [(inv.momento_post(p, est), p["orden"]) for p in feed]
        self.assertEqual(claves, sorted(claves, reverse=True))

    def test_reacciones_segun_decision(self):
        ids = lambda est: {p["id"] for p in inv.feed_visible(est)}
        desmintio = ids(estado(2, ["desmintio_sin_datos"]))
        pidio = ids(estado(2, ["pidio_analisis", "informe_publicado"]))
        self.assertIn("net_alcaldia_desmiente", desmintio)
        self.assertIn("net_nos_mintieron", desmintio)
        self.assertNotIn("net_acueducto_informe", desmintio)
        self.assertIn("net_acueducto_informe", pidio)
        self.assertNotIn("net_nos_mintieron", pidio)

    def test_reaccion_a_decision_aparece_cuando_ocurre(self):
        est = estado(1)
        est["hechos"].append("publico_sin_verificar")
        est["hechos_momento"]["publico_sin_verificar"] = 3
        self.assertNotIn("net_titular_comparte", {p["id"] for p in inv.feed_visible(est)})
        est["momento"] = 3
        self.assertEqual(inv.feed_visible(est)[0]["id"], "net_titular_comparte")

    def test_estado_no_revela_antes_de_investigar(self):
        veneno = inv.POSTS_POR_ID["net_veneno"]
        self.assertEqual(inv.estado_post(veneno, estado(0)), "pendiente")
        self.assertEqual(inv.estado_post(veneno, estado(3, pistas=["captura_recortada"])), "manipulada")
        memo = inv.POSTS_POR_ID["net_memo_salud"]
        self.assertEqual(inv.estado_post(memo, estado(0)), "pendiente")
        self.assertEqual(inv.estado_post(memo, estado(2, pistas=["informe_acueducto"])), "verificada")

    def test_posts_nuevos(self):
        est = estado(0)
        nuevos = inv.posts_nuevos(est)
        self.assertTrue(nuevos)
        est["posts_vistos"] = list(nuevos)
        self.assertEqual(inv.posts_nuevos(est), [])


class Expediente(unittest.TestCase):

    def test_relaciones_no_adelantan_hallazgos(self):
        est = estado(1, pistas=["memo_salud_nova"])
        self.assertEqual(inv.relaciones_conocidas("memo_salud_nova", est), [])
        est = estado(1, pistas=["memo_salud_nova", "captura_veneno"])
        self.assertEqual(inv.relaciones_conocidas("memo_salud_nova", est), ["captura_veneno"])

    def test_hipotesis_refutada_cambia_texto(self):
        est = estado(3, pistas=["hip_nova_creo"])
        antes = inv.contenido_pista("hip_nova_creo", est)
        est["pistas"]["hip_nova_creo"] = "refutado"
        self.assertNotEqual(antes, inv.contenido_pista("hip_nova_creo", est))


class FinalSecreto(unittest.TestCase):

    def test_requiere_las_tres_evidencias(self):
        completas = ["panel_programacion", "anuncio_resonancia", "testimonio_acueducto"]
        self.assertTrue(inv.final_secreto_disponible(estado(4, pistas=completas)))
        for falta in completas:
            self.assertFalse(inv.final_secreto_disponible(estado(4, pistas=[p for p in completas if p != falta])))
        alternativa = ["panel_programacion", "anuncio_resonancia", "informe_acueducto"]
        self.assertTrue(inv.final_secreto_disponible(estado(4, pistas=alternativa)))

    def test_evidencias_clave_no_dependen_de_eventos(self):
        for grupo, ids in inv.PISTAS_CLAVE.items():
            fuentes = []
            for pid in ids:
                if pid in PISTAS_NARRATIVAS:
                    fuentes.append(pid)
                for post in inv.PUBLICACIONES_NET:
                    if post["pista"] == pid and not any(t.startswith("evento:") for t in tokens(post["condicion"])):
                        fuentes.append(post["id"])
            self.assertTrue(fuentes, grupo)


class Eventos(unittest.TestCase):

    def test_reproducible(self):
        for semilla in range(50):
            self.assertEqual(inv.elegir_eventos(semilla), inv.elegir_eventos(semilla))

    def test_coherentes_y_con_cobertura(self):
        vistos = set()
        for semilla in range(300):
            for feria in (False, True):
                elegidos = inv.elegir_eventos(semilla, feria)
                self.assertEqual(inv.problemas_eventos(elegidos), [])
                vistos |= {e for e in elegidos.values() if e}
        self.assertEqual(vistos, set(inv.EVENTOS))

    def test_feria_solo_eventos_seguros(self):
        seguros = {e for pool in inv.POOL_EVENTOS_FERIA.values() for e in pool if e}
        for semilla in range(200):
            for evento in inv.elegir_eventos(semilla, feria=True).values():
                self.assertTrue(evento is None or evento in seguros)

    def test_forzados_para_qa(self):
        elegidos = inv.elegir_eventos(5, forzados={inv.LUNES: "filtracion_martina", inv.DOMINGO: None})
        self.assertEqual(elegidos[inv.LUNES], "filtracion_martina")
        self.assertIsNone(elegidos[inv.DOMINGO])
        ignorado = inv.elegir_eventos(5, forzados={inv.LUNES: "captura_falsa"})
        self.assertNotEqual(ignorado[inv.LUNES], "captura_falsa")


class Puzzle(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.red = crear_red_civitas()
        cls.modos = [
            dict(eslabones=3, senuelos=3),
            dict(eslabones=3, senuelos=3, inferencia=True, rumor=0, hora_base=369, candidatos=["@verdad.oculta"]),
            dict(eslabones=2, senuelos=2, tiempo=75.0, rumor=0, hora_base=369, candidatos=["@verdad.oculta"]),
        ]

    def resolver(self, p):
        p.empezar()
        for i, carta in enumerate(p.solucion):
            p.colocar(carta, i)
        p.elegir_conclusion(p.tipo_origen())
        p.comprobar()
        if p.fase == "inferencia":
            p.responder_inferencia("recortada")
        return p

    def test_siempre_soluble_y_sin_ambiguedad_de_origen(self):
        for semilla in range(150):
            for modo in self.modos:
                p = PuzzleEvidencias(self.red, semilla, **modo)
                self.assertEqual(len(p.cartas), len(set(p.cartas)))
                self.assertNotIn(p.inicio, p.cartas)
                self.assertEqual(p.minutos[p.origen], 0)
                self.assertTrue(all(p.minutos[c] > 0 for c in p.cartas if c != p.origen))
                self.assertTrue(self.resolver(p).exito(), (semilla, modo))

    def test_cadena_equivocada_explica_el_error(self):
        for semilla in range(60):
            p = PuzzleEvidencias(self.red, semilla, **self.modos[1])
            p.empezar()
            senuelos = [c for c in p.cartas if c not in p.solucion]
            for i, carta in enumerate(senuelos[:p.eslabones]):
                p.colocar(carta, i)
            p.elegir_conclusion(p.tipo_origen())
            p.comprobar()
            self.assertFalse(p.exito())
            self.assertTrue(p.explicaciones)
            self.assertEqual(len(p.explicaciones), sum(1 for r in p.revision if r is False))

    def test_pistas_nunca_senalan_senuelos_como_respuesta(self):
        for semilla in range(60):
            p = PuzzleEvidencias(self.red, semilla, **self.modos[0])
            p.empezar()
            receptor, _ = p._primer_error()
            p.pedir_pista()
            self.assertIn(p.solucion[0], p.candidatos_pista)
            self.assertTrue(all(p.puede_ser_fuente(receptor, c) for c in p.candidatos_pista))
            revelada = p.pedir_pista()
            self.assertTrue(p.puede_ser_fuente(p.inicio, revelada))
            self.assertIsNotNone(p.ruta_tablero(revelada, p.eslabones - 1, (revelada,)))

    def test_pista_tras_callejon_sin_salida(self):
        """Un senuelo valido como fuente pero sin camino al origen no deja la pista vacia."""
        revisados = 0
        for semilla in range(200):
            p = PuzzleEvidencias(self.red, semilla, **self.modos[0])
            p.empezar()
            callejones = [c for c in p.cartas if p.puede_ser_fuente(p.inicio, c)
                          and p.ruta_tablero(c, p.eslabones - 1, (c,)) is None]
            if not callejones:
                continue
            revisados += 1
            p.colocar(callejones[0], 0)
            receptor, indice = p._primer_error()
            self.assertEqual((receptor, indice), (p.inicio, 0))
            p.pedir_pista()
            self.assertTrue(p.candidatos_pista)
            revelada = p.pedir_pista()
            self.assertIsNotNone(revelada)
            self.assertNotEqual(revelada, callejones[0])
        self.assertTrue(revisados)

    def test_inferencia_no_castiga_con_derrota(self):
        p = PuzzleEvidencias(self.red, 3, **self.modos[1])
        p.empezar()
        for i, carta in enumerate(p.solucion):
            p.colocar(carta, i)
        p.elegir_conclusion(p.tipo_origen())
        p.comprobar()
        self.assertEqual(p.fase, "inferencia")
        p.tick(500)
        self.assertEqual(p.estado, "jugando")
        p.responder_inferencia("inventada")
        self.assertTrue(p.explicacion_inferencia)
        self.assertEqual(p.estado, "jugando")
        p.responder_inferencia("recortada")
        self.assertTrue(p.exito() and p.resultado()["inferencia"])

    def test_clics_repetidos_y_piezas(self):
        p = PuzzleEvidencias(self.red, 9, **self.modos[0])
        p.empezar()
        carta = p.cartas[0]
        for indice in (0, 1, 2, 0, 0):
            p.colocar(carta, indice)
        self.assertEqual(p.slots.count(carta), 1)
        p.quitar(carta)
        p.quitar(carta)
        self.assertEqual(sorted(p.en_mesa()), sorted(p.cartas))
        self.assertFalse(p.comprobar())
        self.assertEqual(p.comprobaciones_usadas, 0)

    def test_tiempo_agotado_y_guardado(self):
        p = PuzzleEvidencias(self.red, 4, **self.modos[2])
        p.empezar()
        pickle.loads(pickle.dumps(p))
        p.tick(80)
        self.assertEqual(p.estado, "derrota")
        self.assertFalse(p.resultado()["exito"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
