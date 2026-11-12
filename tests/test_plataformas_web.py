"""
Paridad del plataformero: leaderboard/app/static/plat_motor.js (navegador) frente a clases/Plataformas.py.
Las mismas mascaras de entrada, tick a tick, deben dar la misma posicion, velocidad, muertes, evidencias,
estado, puntuacion y traza en los cuatro niveles; y el servidor debe aceptar y puntuar igual la traza del JS.
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

from clases import Plataformas as P  # noqa: E402

MOTOR = os.path.join(RAIZ, "leaderboard", "app", "static", "plat_motor.js")
NODE = shutil.which("node")
RUNNER = r"""
const M = require(process.argv[process.argv.length - 1]);
const casos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(casos.map(c => {
  const p = new M.Partida(c.cfg), huellas = [];
  for (const m of c.mascaras) { p.avanzar(m); if (p.tick % 7 === 0 || !p.jugando()) huellas.push(p.huella()); if (!p.jugando()) break; }
  return {huellas, puntos: p.puntuacion(), traza: p.traza, recogidas: p.recogidas, estado: p.estado};
})));
"""


def mascaras(clave, semilla, habilidad, ruido):
    """Entradas de un piloto con ruido (teclas al azar): cubre muertes, retrocesos y tiempo agotado."""
    rng = random.Random(semilla)
    p = P.Partida(clave)
    piloto = P.Piloto(random.Random(semilla + 1), habilidad)
    lista, huellas = [], []
    while p.jugando():
        m = piloto.mascara(p)
        if rng.random() < ruido:
            m = rng.randrange(8)
        lista.append(m)
        p.avanzar(m)
        if p.tick % 7 == 0 or not p.jugando():
            huellas.append([p.tick, p.x, p.y, p.vx, p.vy, p.muertes, len(p.recogidas), p.estado])
    return lista, huellas, p


@unittest.skipIf(NODE is None, "Node.js no esta instalado")
class TestPlataformasWeb(unittest.TestCase):
    def test_paridad_tick_a_tick_y_traza_aceptada_por_el_servidor(self):
        casos, esperados = [], []
        for clave in P.NIVELES:
            for semilla, hab, ruido in ((1, 1.0, 0.0), (2, 0.6, 0.05), (3, 0.3, 0.2), (4, 1.0, 0.5)):
                lista, huellas, p = mascaras(clave, semilla, hab, ruido)
                casos.append({"cfg": P.config_cliente(clave), "mascaras": lista})
                esperados.append((clave, huellas, p))
        r = subprocess.run([NODE, "-e", RUNNER, MOTOR], input=json.dumps(casos), capture_output=True, text=True, timeout=180)
        self.assertEqual(r.returncode, 0, r.stderr[:500])
        for (clave, huellas, p), js in zip(esperados, json.loads(r.stdout)):
            with self.subTest(nivel=clave, ticks=p.tick):
                self.assertEqual(js["huellas"], huellas)
                self.assertEqual(js["puntos"], p.puntuacion())
                self.assertEqual(js["traza"], p.traza)
                self.assertEqual(js["recogidas"], p.recogidas)
                servidor = P.rejugar(clave, js["traza"])
                self.assertEqual(servidor.puntuacion(), js["puntos"])
        self.assertTrue(any(p.muertes for _, _, p in esperados))
        self.assertTrue(any(p.completado() for _, _, p in esperados))


if __name__ == "__main__":
    unittest.main()
