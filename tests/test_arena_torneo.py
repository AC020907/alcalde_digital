"""
Torneo de Arena: Consejo Civico + 5 pruebas con los minijuegos de Historia + eleccion.
- Motor puro (torneo.py): validadores que rechazan resultados imposibles, puntuacion reproducible,
  mismas condiciones para todos, consecuencias colectivas y campeon distinto del resultado de la ciudad.
- Red: servidor TCP real con 2, 3 y 4 bots (clientes reales) recorriendo todas las fases; desconexion
  durante una prueba, duplicados y resultados fuera de orden.
"""
import os
import random
import sys
import time
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "game"))

from clases.arena import torneo as T  # noqa: E402
from clases.arena.bot import BotArena  # noqa: E402
from clases.arena.cliente import ClienteArena  # noqa: E402
from clases.arena.reglas import Partida  # noqa: E402
from clases.arena.servidor import ServidorArena  # noqa: E402
from clases.moderacion_datos import publicaciones_moderacion  # noqa: E402
from clases.PuzzleEvidencias import PuzzleEvidencias  # noqa: E402
from clases.RedCivitas import crear_red_civitas  # noqa: E402

ROLES4 = ("influencer", "periodista", "ciudadano", "candidato")


def partida(n=3, semilla=7, modo="completo"):
    p = Partida(semilla, rondas=T.MODOS_TORNEO[modo]["rondas_civicas"])
    p.con_torneo = True
    for i in range(n):
        p.unir("j%d" % (i + 1), "P%d" % (i + 1), ROLES4[i])
    return p


def spec(clave, modo="completo", semilla=123):
    return dict(T.preparar_prueba(clave, modo, semilla, dict(Partida().indicadores)), indice=0, total=5)


class TestPuntuacion(unittest.TestCase):
    def test_moderacion_perfecta_y_censura(self):
        s = spec("moderador")
        pubs, _ = publicaciones_moderacion(s["semilla"], s["cantidad"])
        perfecto = T.puntuar(s, {"decisiones": [p.es_falsa for p in pubs]})
        self.assertEqual(perfecto["normalizado"], 1000)
        censor = T.puntuar(s, {"decisiones": [True] * len(pubs)})   # borrar todo = censurar criticas reales
        self.assertGreater(censor["detalle"]["censuras"], 0)
        self.assertLess(censor["normalizado"], 500)

    def test_moderacion_rechaza_formato(self):
        s = spec("moderador")
        for malo in ({"decisiones": "si"}, {"decisiones": [1, 0]}, {"decisiones": [True] * 99}, {}):
            with self.assertRaises(T.ResultadoInvalido):
                T.puntuar(s, malo)

    def test_rastreador_rejuega_los_intentos(self):
        s = spec("rastreador")
        a = s["ajustes"]
        p = PuzzleEvidencias(crear_red_civitas(), s["semilla"], eslabones=a["eslabones"], senuelos=a["senuelos"],
                             tiempo=a["tiempo"])
        bien = [list(p.solucion), p.tipo_origen()]
        r = T.puntuar(s, {"intentos": [bien], "segundos": 30.0, "pistas": 0})
        self.assertTrue(r["detalle"]["origen_encontrado"])
        self.assertGreater(r["normalizado"], 800)
        # Decir "lo encontre" sin una cadena correcta no da la victoria: el servidor la comprueba.
        otra = next(c for c in p.opciones_conclusion if c != p.tipo_origen())
        falso = T.puntuar(s, {"intentos": [[list(reversed(p.solucion)), otra]],
                              "segundos": 10.0, "exito": True})
        self.assertFalse(falso["detalle"]["origen_encontrado"])
        with self.assertRaises(T.ResultadoInvalido):
            T.puntuar(s, {"intentos": [bien], "segundos": 9999})

    def test_bot_experto_encuentra_el_origen_en_todas_las_semillas(self):
        for semilla in range(40):
            for modo in ("completo", "feria"):
                s = spec("rastreador", modo, semilla)
                r = T.puntuar(s, T.payload_bot(s, 1.0, random.Random(0)))
                self.assertTrue(r["detalle"]["origen_encontrado"], (modo, semilla))

    def test_plataformas_se_rejuega_en_el_servidor(self):
        from clases import Plataformas as PL
        s = spec("plataformas")
        bueno = PL.bot(s["nivel"], random.Random(4), 1.0)
        r = T.puntuar(s, {"traza": bueno.traza})
        self.assertEqual(r["normalizado"], bueno.puntuacion())
        self.assertTrue(r["detalle"]["completed"])
        # Enviar "puntos" no sirve de nada: solo cuenta la traza. Sin moverse, 0.
        quieto = T.puntuar(s, {"traza": [[0, 600]], "score_normalized": 1000, "completed": True})
        self.assertEqual(quieto["normalizado"], 0)
        for mala in ({}, {"traza": "x"}, {"traza": [[8, 10]]}, {"traza": [[2, 10 ** 9]]}):
            with self.assertRaises(T.ResultadoInvalido):
                T.puntuar(s, mala)

    def test_arcade_incoherente_rechazado(self):
        s = spec("contencion")
        from clases.ConfigMinijuegos import MODOS
        umbral = MODOS["contencion"].get("umbral_viral", 10000)
        with self.assertRaises(T.ResultadoInvalido):
            T.puntuar(s, {"reposts": umbral * 3, "interceptados": 3, "exito": True})
        with self.assertRaises(T.ResultadoInvalido):
            T.puntuar(s, {"reposts": -5, "interceptados": 3, "exito": False})
        bueno = T.puntuar(s, {"reposts": int(umbral * .2), "interceptados": 20, "exito": True})
        malo = T.puntuar(s, {"reposts": umbral * 2, "interceptados": 0, "exito": False})
        self.assertGreater(bueno["normalizado"], malo["normalizado"])

    def test_duelo_recalcula_en_servidor(self):
        s = spec("ritmo")
        n = s["notas"]
        perfecto = T.puntuar(s, {"dificultad": "normal", "juicios": ["perfect"] * n})
        self.assertEqual(perfecto["normalizado"], 1000)
        with self.assertRaises(T.ResultadoInvalido):        # una nota menos = chart distinto
            T.puntuar(s, {"dificultad": "normal", "juicios": ["perfect"] * (n - 1)})
        with self.assertRaises(T.ResultadoInvalido):        # todos juegan el mismo chart
            T.puntuar(s, {"dificultad": "facil", "juicios": ["perfect"] * n})
        cortado = ["perfect"] * n
        cortado[n // 2] = "miss"
        self.assertLess(T.puntuar(s, {"dificultad": "normal", "juicios": cortado})["detalle"]["max_combo"], n)

    def test_consejo_pesa_mas_que_una_prueba_pero_no_decide_solo(self):
        self.assertEqual(T.puntos_consejo(0, 5), 1000)
        self.assertEqual(T.puntos_consejo(10 ** 6, 5), T.MAX_CONSEJO)
        self.assertEqual(T.puntos_consejo(-10 ** 6, 5), 0)
        total = T.MAX_CONSEJO + T.MAX_PRUEBA * len(T.PRUEBAS)
        self.assertLess(T.MAX_CONSEJO / float(total), .5)
        self.assertGreater(T.MAX_CONSEJO, T.MAX_PRUEBA)


class TestTorneo(unittest.TestCase):
    def jugar(self, n, niveles, modo="completo", semilla=7):
        p = partida(n, semilla, modo)
        t = T.TorneoArena(p, modo)
        rng = random.Random(semilla)
        specs = []
        while True:
            s = t.abrir_siguiente()
            if s is None:
                break
            specs.append(s)
            for jid, nv in zip(p.jugadores, niveles):
                t.entregar(jid, T.payload_bot(s, nv, rng))
            t.cerrar_prueba()
        return p, t, specs

    def test_orden_y_duelo_final(self):
        _, t, specs = self.jugar(2, (.9, .3))
        self.assertEqual([s["clave"] for s in specs], list(T.PRUEBAS))
        self.assertEqual(specs[-1]["clave"], "ritmo")

    def test_reproducible_con_la_misma_semilla(self):
        a = self.jugar(3, (.9, .5, .2))[1].clasificacion()
        b = self.jugar(3, (.9, .5, .2))[1].clasificacion()
        self.assertEqual(a, b)

    def test_mejor_jugador_gana_y_campeon_distinto_de_ciudad(self):
        for n in (2, 3, 4):
            p, t, _ = self.jugar(n, (.95, .5, .3, .1)[:n])
            final = t.final()
            self.assertEqual(final["torneo"]["campeon"], "j1")
            self.assertIn("ganador", final)                 # la eleccion de la ciudad sigue existiendo
            self.assertIn("ciudad", final)
            self.assertEqual(len(final["torneo"]["clasificacion"]), n)

    def test_consecuencias_colectivas_no_reinician_indicadores(self):
        p_bien, _, _ = self.jugar(3, (.95, .9, .9))
        p_mal, _, _ = self.jugar(3, (.05, .05, .05))
        self.assertLess(p_bien.indicadores["desinformacion"], p_mal.indicadores["desinformacion"])
        self.assertGreater(p_bien.indicadores["info_verificada"], p_mal.indicadores["info_verificada"])

    def test_entrega_duplicada_y_jugador_desconocido(self):
        p = partida(2)
        t = T.TorneoArena(p)
        s = t.abrir_siguiente()
        t.entregar("j1", T.payload_bot(s, .8, random.Random(1)))
        with self.assertRaises(T.ResultadoInvalido):
            t.entregar("j1", T.payload_bot(s, 1, random.Random(1)))
        with self.assertRaises(T.ResultadoInvalido):
            t.entregar("j9", T.payload_bot(s, 1, random.Random(1)))

    def test_desconectado_recibe_cero_y_no_bloquea(self):
        p = partida(3)
        t = T.TorneoArena(p)
        s = t.abrir_siguiente()
        p.jugadores["j3"].conectado = False
        for jid in ("j1", "j2"):
            t.entregar(jid, T.payload_bot(s, .8, random.Random(1)))
        self.assertTrue(t.todos_entregaron())
        r = t.cerrar_prueba()
        self.assertEqual(r["resultados"]["j3"]["normalizado"], 0)

    def test_feria_tiene_las_cinco_pruebas_mas_cortas(self):
        _, _, specs = self.jugar(2, (.8, .4), modo="feria")
        self.assertEqual(len(specs), 5)
        for s_feria in specs:      # cada prueba de la Feria dura como mucho lo que su version completa
            self.assertLessEqual(T.limite_segundos(s_feria), T.limite_segundos(spec(s_feria["clave"])))
        self.assertLess(T.limite_segundos(next(x for x in specs if x["clave"] == "plataformas")), T.limite_segundos(spec("plataformas")))

    def test_mismas_condiciones_para_todos(self):
        p = partida(4)
        t = T.TorneoArena(p)
        s = t.abrir_siguiente()
        self.assertEqual(s, t.spec)   # una sola spec por prueba, difundida igual a todos


def esperar(cond, segundos):
    fin = time.monotonic() + segundos
    while time.monotonic() < fin:
        if cond():
            return True
        time.sleep(0.05)
    return cond()


class TestTorneoEnRed(unittest.TestCase):
    def correr(self, n, desconectar=None):
        s = ServidorArena(host="127.0.0.1", puerto=0, semilla=11, rondas=2, segundos=8, pausa_resultado=0.2,
                          torneo="feria", pausa_resumen=0.2, escala_limite=0.05)
        s.iniciar()
        bots = []
        try:
            for i in range(n):
                bots.append(BotArena("127.0.0.1", s.puerto, ROLES4[i], semilla=i, demora=(0.01, 0.05),
                                     nivel=(.95, .6, .4, .2)[i]).iniciar())
                time.sleep(0.1)
            self.assertTrue(esperar(lambda: len(s.listos) == n, 5))
            anfitrion = next(b for b in bots if b.cliente.soy_anfitrion())
            anfitrion.cliente.enviar("empezar")
            if desconectar is not None:
                self.assertTrue(esperar(lambda: s.partida.fase == "prueba", 20))
                bots[desconectar].detener()
            self.assertTrue(esperar(lambda: all(b.cliente.final for b in bots if b.activo), 60), s.registro[-5:])
            finales = [b.cliente.final for b in bots if b.activo]
            self.assertTrue(all(f == finales[0] for f in finales))
            return s, finales[0]
        finally:
            for b in bots:
                b.detener()
            s.detener()

    def test_2_3_4_jugadores_todas_las_fases(self):
        for n in (2, 3, 4):
            with self.subTest(jugadores=n):
                s, final = self.correr(n)
                fases = [e[0] for e in s.registro]
                self.assertEqual(fases.count("prueba"), 5)
                self.assertEqual(fases.count("resumen"), 5)
                self.assertEqual([e[1] for e in s.registro if e[0] == "prueba"], list(T.PRUEBAS))
                self.assertEqual(len(final["torneo"]["clasificacion"]), n)
                self.assertEqual(final["torneo"]["campeon"], "j1")

    def test_desconexion_durante_una_prueba(self):
        s, final = self.correr(3, desconectar=2)
        fila = next(f for f in final["torneo"]["clasificacion"] if f["id"] == "j3")
        self.assertLess(sum(fila["pruebas"].values()), 1000)

    def test_resultado_fuera_de_orden_y_duplicado(self):
        s = ServidorArena(host="127.0.0.1", puerto=0, semilla=5, rondas=2, segundos=8, pausa_resultado=0.2,
                          torneo="feria", pausa_resumen=30, escala_limite=1.0)
        s.iniciar()
        try:
            bot = BotArena("127.0.0.1", s.puerto, "periodista", demora=(0.01, 0.02), nivel=.9).iniciar()
            c = ClienteArena("127.0.0.1", s.puerto)
            c.conectar()
            c.unirse("Humano", "influencer")
            self.assertTrue(c.esperar(lambda c: c.jugador_id, 5))
            c.enviar("listo", listo=True)
            self.assertTrue(esperar(lambda: len(s.listos) == 2, 5))
            (c if c.soy_anfitrion() else bot.cliente).enviar("empezar")
            from clases.arena.bot import elegir_ruta
            rng = random.Random(0)
            hechas = set()
            ok = c.esperar(lambda c: c.prueba is not None or (
                c.ronda and c.ronda["ronda"] not in hechas and not hechas.add(c.ronda["ronda"])
                and c.decidir(elegir_ruta(c.arbol, "responsable", rng)) and False), 30)
            self.assertTrue(ok)
            c.enviar("resultado_prueba", indice=3, datos={"decisiones": []})
            self.assertTrue(c.esperar(lambda c: c.error and "otra prueba" in c.error, 5))
            datos = T.payload_bot(c.prueba, 1.0, rng)
            mid = c.entregar_prueba(datos)
            self.assertTrue(c.esperar(lambda c: c.mi_resultado or c.resumen, 5))
            # mismo id reenviado tras un corte: el servidor no lo cuenta dos veces
            from clases.arena import protocolo
            c.sock.sendall(protocolo.codificar({"tipo": "resultado_prueba", "id": mid, "indice": 0, "datos": datos}))
            self.assertTrue(c.esperar(lambda c: c.resumen is not None, 10))
            self.assertEqual([e[0] for e in s.registro].count("entrega"), 2)
            bot.detener()
            c.cerrar()
        finally:
            s.detener()


if __name__ == "__main__":
    unittest.main()
