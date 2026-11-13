"""Arena Civitas: arbol, grafo, propagacion, indicadores, puntuacion y eleccion (sin red)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from clases.GrafoSocial import GrafoSocial  # noqa: E402
from clases.Tree import ArbolDecisiones  # noqa: E402
from clases.arena import reglas as R  # noqa: E402


def partida(n=4, semilla=11, rondas=5):
    p = R.Partida(semilla=semilla, rondas=rondas)
    for i, rol in enumerate(R.ROLES[:n]):
        assert p.unir("j%d" % i, "J%d" % i, rol) is None
    return p


def ruta_para(arbol, accion):
    """Ruta de indices hasta la hoja con esa consecuencia (recorrido DFS del arbol)."""
    def buscar(nodo, ruta):
        if not nodo["hijos"]:
            return ruta if R_ACCION.get(nodo["etiqueta"]) == accion else None
        for i, h in enumerate(nodo["hijos"]):
            r = buscar(h, ruta + [i])
            if r is not None:
                return r
        return None
    return buscar(arbol, [])


R_ACCION = {"compartir": R.COMPARTIR, "si": R.VERIFICADA, "no": R.REPORTAR_FALSA, "ignorar": R.IGNORAR,
            "reportar": R.REPORTAR, "responder": R.RESPONDER}


def jugar_ronda(p, politica):
    """politica(jugador, publicacion_real) -> accion."""
    p.nueva_ronda()
    for jid, j in p.jugadores.items():
        accion = politica(j, p.publicacion)
        ruta = ruta_para(p.arbol_de(jid), accion)
        if ruta is None:
            ruta = ruta_para(p.arbol_de(jid), R.IGNORAR)
        assert p.registrar_accion(jid, ruta) is None
    return p.resolver_ronda()


def responsable(j, pub):
    if pub["tipo"] == "falsa":
        return R.RESPONDER if j.rol == "candidato" and pub["candidato"] == j.candidato else R.REPORTAR_FALSA
    if pub["tipo"] == "verdadera":
        return R.VERIFICADA
    return R.IGNORAR


def irresponsable(j, pub):
    return R.COMPARTIR if pub["tipo"] != "verdadera" else R.REPORTAR


class TestArbol(unittest.TestCase):
    def test_arbol_del_pdf(self):
        a = R.arbol_base()
        self.assertEqual(a.recorrido_por_niveles()[:5],
                         ["¿Qué quieres hacer?", "Compartir", "¿Es verdadera?", "Ignorar", "Reportar"])
        self.assertEqual(a.altura(), 3)
        self.assertEqual(a.tamanio(), 7)
        self.assertEqual([h.consecuencia for h in a.hojas()],
                         [R.COMPARTIR, R.VERIFICADA, R.REPORTAR_FALSA, R.IGNORAR, R.REPORTAR])

    def test_insertar_buscar_eliminar_y_recorrer(self):
        a = ArbolDecisiones()
        raiz = a.insertar_raiz("r")
        x = a.insertar_hijo(raiz, "x", etiqueta="x")
        a.insertar_hijo(x, "x1", etiqueta="x1")
        a.insertar_hijo(raiz, "y", etiqueta="y")
        self.assertEqual(a.preorden(a.raiz), ["r", "x", "x1", "y"])
        self.assertEqual(a.posorden(a.raiz), ["x1", "x", "y", "r"])
        self.assertIs(a.buscar("x1").padre, x)
        self.assertTrue(a.eliminar(x))
        self.assertIsNone(a.buscar("x1"))
        self.assertEqual(a.preorden(a.raiz), ["r", "y"])
        self.assertFalse(a.eliminar(x))
        self.assertIsNone(a.recorrer_ruta([5]))
        self.assertIsNone(a.recorrer_ruta([True]))

    def test_candidato_no_reporta_lo_suyo_y_puede_responder(self):
        pub = R.POR_ID["prado_robo"]
        a = R.arbol_para("candidato", pub, "prado")
        etiquetas = [h.etiqueta for h in a.raiz.hijos]
        self.assertNotIn("reportar", etiquetas)
        self.assertIn("responder", etiquetas)
        b = R.arbol_para("candidato", R.POR_ID["colegio"], "prado")
        self.assertIn("reportar", [h.etiqueta for h in b.raiz.hijos])

    def test_periodista_ve_la_fuente_y_los_demas_una_pista(self):
        pub = R.POR_ID["agua"]
        self.assertIn(pub["fuente"], R.arbol_para("periodista", pub, None).buscar("verificar").texto)
        self.assertIn(pub["pista"], R.arbol_para("ciudadano", pub, None).buscar("verificar").texto)


class TestGrafos(unittest.TestCase):
    def test_operaciones_basicas(self):
        g = GrafoSocial()
        g.agregar_conexion("ana", "luis", .5)
        g.agregar_conexion("luis", "ana", .5)
        g.agregar_conexion("luis", "carlos", .5)
        self.assertTrue(g.eliminar_conexion("ana", "luis"))
        self.assertFalse(g.existe_conexion("ana", "luis"))
        self.assertTrue(g.eliminar_usuario("luis"))
        self.assertEqual(g.aristas(), [])
        self.assertFalse(g.existe("luis"))
        self.assertEqual(g.predecesores("carlos"), [])

    def test_grafo_social_del_pdf_y_ciclos(self):
        g = R.construir_grafo_social()
        for a, b in (("ana", "luis"), ("ana", "pedro"), ("luis", "carlos"), ("pedro", "maria"), ("carlos", "maria")):
            self.assertTrue(g.existe_conexion(a, b))
        # carlos <-> maria es un ciclo: el BFS no se queda dando vueltas y no repite nodos.
        recorrido = g.bfs_recorrido("ana")
        self.assertEqual(len(recorrido), len(set(recorrido)))

    def test_grafo_ciudad_y_distancias(self):
        c = R.construir_grafo_ciudad()
        d = R.distancias_zona(c, "colegio")
        self.assertEqual(d, {"colegio": 0, "barrio": 1, "parque": 2, "plaza": 2, "alcaldia": 3})

    def test_bfs_multifuente_bloqueos_y_aislados(self):
        g = R.construir_grafo_social()
        g.agregar_usuario("solo", "Solo")
        niveles = g.bfs_multifuente(["ana", "pedro"])
        alcanzados = {n for nivel in niveles for n in nivel}
        self.assertNotIn("solo", alcanzados)
        bloqueado = g.bfs_multifuente(["ana"], bloqueados={"luis", "pedro", "diego"})
        self.assertEqual(bloqueado, [["ana"]])

    def test_misma_semilla_misma_propagacion(self):
        g = R.construir_grafo_social()
        self.assertEqual(g.bfs_multifuente(["ana"], semilla="s1"), g.bfs_multifuente(["ana"], semilla="s1"))


class TestPartida(unittest.TestCase):
    def test_roles_unicos_y_limites(self):
        p = R.Partida()
        self.assertIsNone(p.unir("a", "A", "ciudadano"))
        self.assertIsNotNone(p.unir("b", "B", "ciudadano"))
        self.assertIsNotNone(p.unir("b", "B", "hechicero"))
        self.assertFalse(p.puede_empezar())
        for i, rol in enumerate(("periodista", "influencer", "candidato")):
            p.unir("x%d" % i, "X", rol)
        self.assertTrue(p.puede_empezar())

    def test_jugadores_entran_al_grafo(self):
        p = partida(4)
        self.assertGreater(len(p.grafo.vecinos("j:j2")), len(p.grafo.vecinos("j:j0")))  # influencer > ciudadano
        p2 = R.Partida()
        p2.unir("a", "A", "ciudadano")
        p2.quitar("a")
        self.assertFalse(p2.grafo.existe("j:a"))

    def test_misma_semilla_misma_partida_y_semillas_distintas_varian(self):
        def recorrido(semilla):
            p = partida(3, semilla)
            return [(jugar_ronda(p, responsable)["publicacion"]["id"]) for _ in range(5)]
        self.assertEqual(recorrido(5), recorrido(5))
        self.assertGreater(len({tuple(recorrido(s)) for s in range(6)}), 1)

    def test_accion_invalida_duplicada_o_fuera_de_ronda(self):
        p = partida(2)
        self.assertIsNotNone(p.registrar_accion("j0", [0]))      # aun no hay ronda
        p.nueva_ronda()
        self.assertIsNotNone(p.registrar_accion("j0", [1]))      # nodo interno, no hoja
        self.assertIsNotNone(p.registrar_accion("j0", [9]))
        self.assertIsNotNone(p.registrar_accion("zz", [0]))
        self.assertIsNone(p.registrar_accion("j0", [0]))
        self.assertIsNotNone(p.registrar_accion("j0", [2]))      # solo cuenta la primera

    def test_sin_respuesta_penaliza(self):
        p = partida(2)
        p.nueva_ronda()
        r = p.resolver_ronda()
        self.assertTrue(all(a["accion"] == R.SIN_RESPUESTA and a["puntos"] < 0 for a in r["acciones"]))

    def test_reportes_frenan_la_propagacion_del_rumor(self):
        def alcance(politica):
            p = partida(4, semilla=3)
            p.nueva_ronda()
            p.publicacion = R.POR_ID["agua"]
            p.usadas[-1] = "agua"
            p.evento = dict(R.EVENTOS["noticia_falsa"], clave="noticia_falsa")
            p.arboles = {jid: R.arbol_para(j.rol, p.publicacion, j.candidato) for jid, j in p.jugadores.items()}
            for jid, j in p.jugadores.items():
                p.registrar_accion(jid, ruta_para(p.arbol_de(jid), politica(j, p.publicacion)))
            return p.resolver_ronda()
        mal, bien = alcance(irresponsable), alcance(responsable)
        self.assertGreater(mal["n_alcanzados"], bien["n_alcanzados"])
        self.assertGreater(mal["delta_indicadores"]["desinformacion"], bien["delta_indicadores"]["desinformacion"])
        self.assertTrue(bien["desmentida"])
        self.assertGreater(len(bien["protegidos"]), 0)
        # Cada nodo alcanzado (salvo las fuentes) tiene un padre que le envio la publicacion por una arista real.
        fuentes = set(bien["niveles"][0]) if bien["niveles"] else set()
        for hijo, padre in mal["padres"].items():
            self.assertTrue(R.construir_grafo_social().existe_conexion(padre, hijo) or padre.startswith("j:"))
            self.assertNotIn(hijo, fuentes)

    def test_responsables_ganan_puntos_y_la_ciudad_mejora(self):
        buenos, malos = partida(4, 9), partida(4, 9)
        for _ in range(5):
            jugar_ronda(buenos, responsable)
            jugar_ronda(malos, irresponsable)
        self.assertTrue(all(j.puntos > 0 for j in buenos.jugadores.values()))
        self.assertTrue(all(j.puntos < 0 for j in malos.jugadores.values()))
        self.assertGreater(buenos.resultado_ciudad()["indice"], malos.resultado_ciudad()["indice"])
        for p in (buenos, malos):
            self.assertTrue(all(0 <= v <= 100 for v in p.indicadores.values()))

    def test_influencer_pesa_el_doble(self):
        p = partida(4)
        j_inf = p.jugadores["j2"]
        j_ciu = p.jugadores["j0"]
        self.assertEqual(p._valorar(j_inf, R.COMPARTIR, "falsa", R.POR_ID["agua"])[0],
                         2 * p._valorar(j_ciu, R.COMPARTIR, "falsa", R.POR_ID["agua"])[0])

    def test_eleccion_depende_de_la_partida(self):
        for n in (2, 3, 4):
            p = partida(n, 21)
            for _ in range(5):
                jugar_ronda(p, responsable)
            e = p.cerrar_resultado()
            self.assertEqual(p.fase, "final")
            self.assertEqual(sum(e["votos"].values()) + e["abstencion"], len(R.CIUDADANOS))
            self.assertIn(e["ganador"], dict(R.CANDIDATOS))
            self.assertTrue(e["explicacion"])
            self.assertEqual(len(e["ranking"]), n)

    def test_participacion_cambia_la_abstencion(self):
        alta, baja = partida(2, 4), partida(2, 4)
        alta.indicadores["participacion"], baja.indicadores["participacion"] = 100, 0
        self.assertLess(alta.elegir_alcalde()["abstencion"], baja.elegir_alcalde()["abstencion"])

    def test_rumores_cambian_el_ganador(self):
        """La eleccion responde a lo que paso: rumores sin desmentir contra un candidato le quitan votos."""
        def votos_prado(desmentir):
            p = partida(2, 13)
            for _ in range(3):
                p.nueva_ronda()
                p.publicacion = R.POR_ID["prado_robo"]
                p.evento = dict(R.EVENTOS["viral"], clave="viral")
                p.arboles = {jid: R.arbol_para(j.rol, p.publicacion, j.candidato) for jid, j in p.jugadores.items()}
                for jid, j in p.jugadores.items():
                    acc = R.REPORTAR_FALSA if desmentir else R.COMPARTIR
                    p.registrar_accion(jid, ruta_para(p.arbol_de(jid), acc))
                p.resolver_ronda()
            return sum(v["prado"] for v in p.confianza_cand.values())
        self.assertGreater(votos_prado(True), votos_prado(False))

    def test_vistas_no_revelan_la_verdad_antes_de_tiempo(self):
        p = partida(2)
        vista = p.nueva_ronda()
        self.assertNotIn("tipo", vista["publicacion"])
        self.assertNotIn("fuente", vista["publicacion"])
        r = p.resolver_ronda()
        self.assertIn(r["publicacion"]["tipo"], ("falsa", "verdadera", "opinion"))


if __name__ == "__main__":
    unittest.main()
