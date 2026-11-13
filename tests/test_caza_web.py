"""
Caza-Rumores online: motor (clases/arena/caza_web.py), validacion por rejuego y paridad con caza_motor.js.
"""
import json
import os
import random
import shutil
import subprocess
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "game"))

from clases.arena import caza_web as C  # noqa: E402

MOTOR = os.path.join(RAIZ, "leaderboard", "app", "static", "caza_motor.js")
NODE = shutil.which("node")
RUNNER = r"""
const M = require(process.argv[process.argv.length - 1]);
const casos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(casos.map(c => {
  const g = new M.Caza(c.cfg), huellas = [], porTick = {};
  for (const t of c.toques) (porTick[t[0]] = porTick[t[0]] || []).push(t);
  while (!g.terminado()) {
    for (const t of (porTick[g.tick + 1] || [])) {
      const cerca = g.buscar(t[2], t[3], c.cfg.radio_toque);     // el navegador encuentra el paquete por posicion
      if (cerca !== t[1] && !g.enVuelo(t[1])) throw new Error('toque invalido');
      g.interceptar(t[1]);
    }
    g.avanzar(); huellas.push(g.huella());
  }
  return {huellas, contagiados: g.nContagiados(), orden: g.orden};
})));
"""


class TestCaza(unittest.TestCase):
    def test_escenario_identico_y_reproducible(self):
        a, b = C.config("feria", 77), C.config("feria", 77)
        self.assertEqual(a, b)
        self.assertNotEqual(a["focos"], C.config("feria", 78)["focos"] + ["x"])
        self.assertEqual(len(a["nodos"]), 16)
        posiciones = {(n["x"], n["y"]) for n in a["nodos"]}
        self.assertEqual(len(posiciones), 16)                         # ninguna cuenta encima de otra
        for n in a["nodos"]:
            self.assertTrue(40 <= n["x"] <= C.ANCHO - 40 and 20 <= n["y"] <= C.ALTO - 10)

    def test_sin_jugador_el_rumor_se_extiende_y_interceptar_lo_frena(self):
        for modo in C.MODOS:
            cfg = C.config(modo, 5)
            base = C.sin_jugador(cfg)
            self.assertGreater(base, len(cfg["focos"]) + 6)
            experto = C.puntuar(cfg, C.toques_bot(cfg, 1.0, random.Random(1)))
            torpe = C.puntuar(cfg, C.toques_bot(cfg, 0.3, random.Random(1)))
            nada = C.puntuar(cfg, {"toques": [], "fallos": 0})
            self.assertEqual(nada["normalizado"], 0)
            self.assertGreater(experto["normalizado"], torpe["normalizado"])
            self.assertGreater(experto["normalizado"], 900)
            self.assertLess(experto["detalle"]["contagiadas"], base)

    def test_toques_manipulados(self):
        cfg = C.config("feria", 9)
        buenos = C.toques_bot(cfg, 0.9, random.Random(2))["toques"]
        self.assertTrue(buenos)
        t0 = buenos[0]
        casos = [
            "x", [[1, 2]], [[True, 0, 1, 1]], [[0, 0, 1, 1]], [[10 ** 6, 0, 1, 1]],
            [[5, 0, 10, 10], [3, 0, 10, 10]],                              # fuera de orden
            [[1, 0, 500, 300]],                                            # paquete que aun no existe
            [[t0[0], t0[1], (t0[2] + 500) % 1000, t0[3]]],                 # lejos del rumor
            [t0, [t0[0] + 1, t0[1], t0[2], t0[3]]],                        # el mismo rumor dos veces
            [[1, 0, 1, 1]] * (C.MAX_TOQUES + 1),
        ]
        for toques in casos:
            with self.assertRaises(C.ToquesInvalidos):
                C.puntuar(cfg, {"toques": toques, "fallos": 0})
        with self.assertRaises(C.ToquesInvalidos):
            C.puntuar(cfg, {"toques": buenos, "fallos": -3})

    def test_fallar_disparos_baja_la_punteria(self):
        cfg = C.config("feria", 9)
        t = C.toques_bot(cfg, 1.0, random.Random(2))["toques"]
        self.assertGreater(C.puntuar(cfg, {"toques": t, "fallos": 0})["normalizado"],
                           C.puntuar(cfg, {"toques": t, "fallos": 40})["normalizado"])

    @unittest.skipIf(NODE is None, "Node.js no esta instalado")
    def test_paridad_con_el_motor_del_navegador(self):
        casos, esperados = [], []
        for modo in C.MODOS:
            for semilla, nivel in ((1, 1.0), (2, 0.7), (3, 0.3), (4, 0.0)):
                cfg = C.config(modo, semilla)
                toques = C.toques_bot(cfg, nivel, random.Random(semilla))["toques"] if nivel else []
                c = C.Caza(cfg)
                huellas, por_tick = [], {}
                for t in toques:
                    por_tick.setdefault(t[0], []).append(t)
                while not c.terminado():
                    for t in por_tick.get(c.tick + 1, ()):
                        c.interceptar(t[1])
                    c.avanzar()
                    huellas.append(c.huella())
                casos.append({"cfg": cfg, "toques": toques})
                esperados.append((huellas, c))
        r = subprocess.run([NODE, "-e", RUNNER, MOTOR], input=json.dumps(casos), capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[:600])
        for (huellas, c), js in zip(esperados, json.loads(r.stdout)):
            self.assertEqual(js["huellas"], huellas)
            self.assertEqual(js["orden"], c.orden)


if __name__ == "__main__":
    unittest.main()
