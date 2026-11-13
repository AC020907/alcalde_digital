"""
Equivalencia del motor ritmico del navegador (leaderboard/app/static/ritmo_motor.js) con Ritmo.Duelo.

Se generan sesiones de juego (pulsaciones con error humano, notas olvidadas, toques al aire) y frames a
30, 60 y 144 Hz con jitter; las MISMAS secuencias se ejecutan en Python y en Node. Deben coincidir juicio a
juicio, en combo maximo, precision y puntos. Tambien se prueba la sincronizacion del reloj con latencia
simulada (RTT asimetrico y picos) y que el resultado del navegador lo acepta el validador del servidor.
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

from clases.Ritmo import Duelo, VENTANAS_MS, VALOR_JUICIO  # noqa: E402
from clases.arena import duelo_online as DO  # noqa: E402
from clases.arena.torneo import puntuar_ritmo  # noqa: E402

MOTOR = os.path.join(RAIZ, "leaderboard", "app", "static", "ritmo_motor.js")
NODE = shutil.which("node")

RUNNER = r"""
const M = require(process.argv[process.argv.length - 1]);
const datos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const salida = datos.sesiones.map(s => {
  const m = new M.MotorDuelo(datos.chart, datos.ventanas, datos.valores);
  m.empezar();
  for (const ev of s) { if (ev[0] === 'f') m.actualizar(ev[1]); else { m.actualizar(ev[1]); m.pulsar(ev[2], ev[1]); } }
  return {juicios: m.notas.map(n => n.estado), max_combo: m.maxCombo, precision: m.precision(), puntos: m.puntos(),
          resultado: m.resultado(), estado: m.estado};
});
const sync = datos.sync.map(c => { const r = new M.SyncReloj(); let e = null;
  for (const mu of c) e = r.agregar(mu[0], mu[1], mu[2]); return e; });
process.stdout.write(JSON.stringify({salida, sync}));
"""


def sesion(chart, hz, rng, habilidad):
    eventos = []
    for n in chart["notes"]:
        r = rng.random()
        if r < habilidad:
            eventos.append(("p", n["time_ms"] + rng.gauss(0, 30 + (1 - habilidad) * 80), n["lane"]))
        elif r < habilidad + 0.1:
            eventos.append(("p", n["time_ms"] + rng.uniform(-300, 300), rng.randrange(4)))   # toque al aire
    t, periodo = 0.0, 1000.0 / hz
    while t <= chart["duration_ms"] + 400:
        eventos.append(("f", t))
        t += periodo * rng.uniform(0.8, 1.25)       # jitter de frames
    eventos.sort(key=lambda e: (e[1], e[0] == "f"))
    return [[e[0], round(e[1], 3)] + ([e[2]] if e[0] == "p" else []) for e in eventos]


def jugar_python(chart, eventos):
    d = Duelo(chart)
    d.empezar()
    for ev in eventos:
        d.actualizar(ev[1])
        if ev[0] == "p":
            d.pulsar(ev[2], ev[1])
    return d


@unittest.skipIf(NODE is None, "Node.js no esta instalado")
class TestMotorWeb(unittest.TestCase):
    def ejecutar(self, chart, sesiones, sync=()):
        entrada = json.dumps({"chart": chart, "ventanas": VENTANAS_MS, "valores": VALOR_JUICIO,
                              "sesiones": sesiones, "sync": list(sync)})
        r = subprocess.run([NODE, "-e", RUNNER, MOTOR], input=entrada, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_equivalencia_con_ritmo_duelo_a_30_60_144_hz(self):
        for modo in ("feria", "historia"):
            chart = DO.cargar_chart(modo)
            rng = random.Random(modo)
            casos = [(hz, hab) for hz in (30, 60, 144) for hab in (0.95, 0.7, 0.4)]
            sesiones = [sesion(chart, hz, rng, hab) for hz, hab in casos]
            js = self.ejecutar(chart, sesiones)["salida"]
            for (hz, hab), ev, r in zip(casos, sesiones, js):
                py = jugar_python(chart, ev)
                with self.subTest(modo=modo, hz=hz, habilidad=hab):
                    self.assertEqual(r["juicios"], [n["estado"] for n in py.notas])
                    self.assertEqual(r["max_combo"], py.max_combo)
                    self.assertAlmostEqual(r["precision"], py.precision(), places=9)
                    self.assertEqual(r["estado"], py.estado)
                    # El resultado que envia el navegador lo acepta el servidor y puntua lo mismo.
                    srv = DO.validar_y_puntuar(chart, r["resultado"], 10 ** 9)
                    self.assertEqual(srv["normalizado"], r["puntos"])
                    self.assertEqual(srv["normalizado"], puntuar_ritmo({}, r["resultado"], chart=chart)["normalizado"])

    def test_sincronizacion_con_latencia_simulada(self):
        rng = random.Random(7)
        casos, esperados = [], []
        for _ in range(60):
            desfase = rng.uniform(-5e6, 5e6)        # reloj local arbitrario respecto al servidor
            inicio_srv = 100000.0
            ida_min, vuelta_min = rng.uniform(15, 150), rng.uniform(15, 150)
            muestras, t_srv = [], inicio_srv - 9000
            for k in range(9):                        # ~9 consultas durante la cuenta atras
                ida = ida_min + rng.expovariate(1 / 60.0) * (3 if rng.random() < 0.2 else 1)   # picos
                vuelta = vuelta_min + rng.expovariate(1 / 60.0)
                enviado = t_srv - ida + desfase
                recibido = t_srv + vuelta + desfase
                muestras.append([enviado, recibido, inicio_srv - t_srv])
                t_srv += 1000
            casos.append(muestras)
            esperados.append((inicio_srv + desfase, abs(ida_min - vuelta_min) / 2))
        est = self.ejecutar(DO.cargar_chart("feria"), [], casos)["sync"]
        errores = [abs(e - real) for e, (real, _) in zip(est, esperados)]
        # Error teorico: asimetria de la ruta / 2 (+ ruido). Debe quedar dentro de la ventana Good (90 ms) y,
        # en cualquier caso, la calibracion corrige un desfase constante igual para todas las notas.
        for err, (_, asim) in zip(errores, esperados):
            self.assertLess(err, asim + 60)
        self.assertLess(sorted(errores)[len(errores) // 2], 45)


if __name__ == "__main__":
    unittest.main()
