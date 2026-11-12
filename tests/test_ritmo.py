"""Duelo de Frecuencias (clases/Ritmo.py): charts, juicio, reloj de cancion y puntuacion."""
import glob
import json
import os
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "game"))

from clases import Ritmo as R  # noqa: E402
from clases import Puntuacion as P  # noqa: E402


def chart(notas, duracion=10000):
    return {"song_id": "t", "version": 1, "bpm": 120, "offset_ms": 0, "difficulty": "normal",
            "duration_ms": duracion, "notes": [{"time_ms": t, "lane": l, "type": "tap"} for t, l in notas]}


def jugando(notas, **kw):
    d = R.Duelo(chart(notas), **kw)
    d.empezar()
    return d


class Charts(unittest.TestCase):
    def test_validos_e_invalidos(self):
        self.assertEqual(R.validar_chart(chart([(1000, 0), (1000, 1), (1500, 0)])), [])
        self.assertTrue(R.validar_chart(chart([(1000, 4)])))                 # carril
        self.assertTrue(R.validar_chart(chart([(2000, 0), (1000, 1)])))      # orden
        self.assertTrue(R.validar_chart(chart([(1000, 0), (1050, 0)])))      # mismo carril demasiado cerca
        self.assertTrue(R.validar_chart(chart([(20000, 0)])))                # fuera de la cancion
        self.assertTrue(R.validar_chart(dict(chart([(1000, 0)]), bpm=0)))
        malo = chart([(1000, 0)])
        del malo["offset_ms"]
        self.assertTrue(R.validar_chart(malo))
        with self.assertRaises(ValueError):
            R.Duelo(chart([]))

    def test_charts_del_juego_validos_y_sincronizados_con_el_audio(self):
        import soundfile as sf
        archivos = sorted(glob.glob(os.path.join(RAIZ, "game", "ritmo", "duelo_*.json")))
        self.assertEqual(len(archivos), 4)
        for ruta in archivos:
            with open(ruta, encoding="utf-8") as f:
                c = json.load(f)
            self.assertEqual(R.validar_chart(c), [], ruta)
            modo = c["song_id"].split("_")[1]
            info = sf.info(os.path.join(RAIZ, "game", "assets", "audio", "music", "duelo_%s.ogg" % modo))
            self.assertAlmostEqual(info.duration * 1000, c["duration_ms"], delta=60)
            # 120 BPM: toda nota cae en la rejilla de semicorcheas (125 ms) del audio.
            for n in c["notes"]:
                self.assertEqual(n["time_ms"] % 125, 0, ruta)
            if c["difficulty"] == "facil":
                tiempos = [n["time_ms"] for n in c["notes"]]
                self.assertEqual(len(tiempos), len(set(tiempos)), "el facil no tiene acordes (tactil)")


class Juicio(unittest.TestCase):
    def test_ventanas(self):
        d = jugando([(1000, 0), (2000, 1), (3000, 2), (4000, 3)])
        self.assertEqual(d.pulsar(0, 1030), "perfect")
        self.assertEqual(d.pulsar(1, 2080), "good")
        self.assertEqual(d.pulsar(2, 2870), "bad")
        self.assertIsNone(d.pulsar(3, 3700))          # demasiado pronto: ni acierta ni falla
        self.assertEqual(d.pulsar(3, 4000), "perfect")

    def test_una_pulsacion_un_juicio_y_sin_dobles(self):
        d = jugando([(1000, 0)])
        self.assertEqual(d.pulsar(0, 1000), "perfect")
        self.assertIsNone(d.pulsar(0, 1010))           # repetir la tecla no vuelve a puntuar
        self.assertEqual(d.juzgadas(), 1)

    def test_acorde_necesita_dos_carriles(self):
        d = jugando([(1000, 1), (1000, 2)])
        self.assertEqual(d.pulsar(1, 1000), "perfect")
        self.assertIsNone(d.pulsar(1, 1005))
        self.assertEqual(d.pulsar(2, 1005), "perfect")

    def test_pulsar_al_aire_no_puntua_ni_castiga(self):
        d = jugando([(1000, 0)])
        for t in range(0, 800, 50):
            self.assertIsNone(d.pulsar(3, t))
        self.assertEqual(d.combo, 0)
        self.assertEqual(d.juzgadas(), 0)

    def test_miss_una_sola_vez_y_combo(self):
        d = jugando([(1000, 0), (1500, 0), (2000, 0)])
        d.pulsar(0, 1000)
        d.pulsar(0, 1500)
        self.assertEqual(d.combo, 2)
        for t in (2200, 2400, 2600, 3000):
            d.actualizar(t)
        self.assertEqual(d.conteo["miss"], 1)
        self.assertEqual(d.combo, 0)
        self.assertEqual(d.max_combo, 2)

    def test_fin_resultados_y_precision(self):
        d = jugando([(1000, 0), (2000, 1)], )
        d.pulsar(0, 1000)
        d.actualizar(10000)
        self.assertEqual(d.estado, R.RESULTS)
        self.assertAlmostEqual(d.precision(), 0.5)
        self.assertFalse(d.exito())
        r = d.resultado()
        self.assertEqual(r["minijuego"], "ritmo")
        self.assertIn(r["calificacion"], ("S", "A", "B", "C", "D"))

    def test_perfecto_y_pausa(self):
        d = jugando([(1000, 0), (2000, 1)])
        d.pausar()
        self.assertIsNone(d.pulsar(0, 1000))           # en pausa no se juzga
        d.actualizar(5000)
        self.assertEqual(d.juzgadas(), 0)              # ni se marcan fallos
        d.reanudar()
        d.pulsar(0, 1000)
        d.pulsar(1, 2000)
        d.actualizar(10000)
        self.assertTrue(d.exito())
        self.assertEqual(d.calificacion(), "S")

    def test_abandono(self):
        d = jugando([(1000, 0)])
        d.abortar()
        self.assertEqual(d.estado, R.ABORTED)
        self.assertTrue(d.resultado()["abandonado"])
        self.assertFalse(d.resultado()["exito"])

    def test_asistido_es_mas_permisivo(self):
        normal = jugando([(1000, 0)])
        asistido = jugando([(1000, 0)], ventanas={"perfect": 70, "good": 140, "bad": 210}, umbral=0.45)
        self.assertIsNone(normal.pulsar(0, 1180))
        self.assertEqual(asistido.pulsar(0, 1180), "bad")

    def test_fps_no_cambia_el_resultado(self):
        toques = [(0, 1000), (1, 1520), (2, 2060), (3, 2510)]
        notas = [(1000, 0), (1500, 1), (2000, 2), (2500, 3), (3000, 0)]
        resultados = []
        for fps in (30, 60, 144):
            d = jugando(notas)
            paso = 1000.0 / fps
            t = 0.0
            pendientes = list(toques)
            while t < 10000:
                while pendientes and pendientes[0][1] <= t:
                    carril, tt = pendientes.pop(0)
                    d.pulsar(carril, tt)               # la entrada lleva su propio tiempo de cancion
                d.actualizar(t)
                t += paso
            resultados.append((dict(d.conteo), d.max_combo, d.estado))
        self.assertEqual(resultados[0], resultados[1])
        self.assertEqual(resultados[1], resultados[2])

    def test_solo_dibuja_visibles(self):
        d = jugando([(t, t // 500 % 4) for t in range(1000, 9001, 500)])
        vis = d.visibles(2000, 1500)
        self.assertTrue(all(1850 <= n["time_ms"] <= 3500 for n in vis))
        self.assertLess(len(vis), 6)


class Reloj(unittest.TestCase):
    def test_audio_none_al_inicio(self):
        r = R.RelojCancion()
        self.assertEqual(r.actualizar(None, 100.0), 0.0)     # sin posicion real no avanza
        self.assertAlmostEqual(r.actualizar(0.5, 100.5), 500.0)

    def test_extrapola_si_el_audio_deja_de_informar_y_mide_drift(self):
        r = R.RelojCancion()
        r.actualizar(1.0, 10.0)
        self.assertAlmostEqual(r.actualizar(None, 10.2), 1200.0)
        r.actualizar(1.25, 10.25)
        self.assertLess(r.drift_max(), 5)

    def test_posicion_por_bloques_no_congela_la_cancion(self):
        r = R.RelojCancion()
        r.actualizar(1.0, 10.0)
        self.assertAlmostEqual(r.actualizar(1.0, 10.016), 1016.0)   # mismo bloque: extrapola
        self.assertAlmostEqual(r.actualizar(1.0, 10.032), 1032.0)
        self.assertAlmostEqual(r.actualizar(1.046, 10.046), 1046.0)  # bloque nuevo: resincroniza

    def test_respaldo_si_el_audio_nunca_informa(self):
        r = R.RelojCancion()
        self.assertEqual(r.actualizar(None, 100.0), 0.0)
        self.assertEqual(r.actualizar(None, 101.0), 0.0)            # espera al audio
        self.assertAlmostEqual(r.actualizar(None, 102.0), 2000.0)   # tras 1,5 s: reloj de pared
        self.assertAlmostEqual(r.actualizar(2.1, 102.1), 2100.0)    # el audio aparece: manda el audio

    def test_offset_de_calibracion(self):
        r = R.RelojCancion(offset_ms=40)
        self.assertAlmostEqual(r.actualizar(1.0, 5.0), 960.0)

    def test_no_retrocede_ni_salta_al_reanudar(self):
        r = R.RelojCancion()
        r.actualizar(2.0, 10.0)
        self.assertEqual(r.actualizar(1.99, 10.01), 2000.0)   # jitter hacia atras: se ignora
        r.pausar()
        self.assertEqual(r.actualizar(None, 20.0), 2000.0)    # en pausa el tiempo no corre
        r.reanudar()
        self.assertEqual(r.actualizar(None, 25.0), 2000.0)    # sin posicion real tras reanudar: espera
        self.assertAlmostEqual(r.actualizar(2.05, 25.05), 2050.0)


class PuntuacionConDuelo(unittest.TestCase):
    def test_cinco_retos_maximo_200_y_total_1000(self):
        self.assertIn("ritmo", P.MINIJUEGOS)
        todo = {m: {"exito": True, "calificacion": "S"} for m in P.MINIJUEGOS}
        self.assertEqual(P.puntos_minijuegos(todo), 200)
        sin_duelo = dict(todo)
        del sin_duelo["ritmo"]
        self.assertEqual(P.puntos_minijuegos(sin_duelo), 160)

    def test_duelo_perdido_no_hunde_la_puntuacion(self):
        base = {m: {"exito": True, "calificacion": "A"} for m in P.MINIJUEGOS}
        perdido = dict(base, ritmo={"exito": False, "calificacion": "D"})
        self.assertGreaterEqual(P.puntos_minijuegos(perdido), P.puntos_minijuegos(base) - 30)


if __name__ == "__main__":
    unittest.main()
