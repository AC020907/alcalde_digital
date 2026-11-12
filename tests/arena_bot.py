"""
Jugador automatico de la Arena como PROCESO independiente (cliente TCP real).

    python tests/arena_bot.py --host 127.0.0.1 --puerto 50777 --rol periodista --politica responsable --salida bot.json

Sirve para las pruebas multiproceso y para llenar una sala en la feria cuando faltan jugadores.
politica: responsable | irresponsable | azar | callado (no responde nunca: prueba el tiempo limite)
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game"))

from clases.arena.bot import elegir_ruta  # noqa: E402,F401
from clases.arena.cliente import ClienteArena  # noqa: E402
from clases.arena.torneo import payload_bot  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--puerto", type=int, required=True)
    ap.add_argument("--rol", required=True)
    ap.add_argument("--nombre", default=None)
    ap.add_argument("--politica", default="responsable")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--limite", type=float, default=240)
    args = ap.parse_args()
    rng = random.Random("%s|%s" % (args.semilla, args.rol))
    import time
    c = ClienteArena(args.host, args.puerto)
    fin = time.monotonic() + 90
    while True:   # el servidor puede tardar en abrir (p. ej. un Ren'Py que aun arranca)
        try:
            c.conectar()
            break
        except OSError:
            if time.monotonic() > fin:
                raise
            time.sleep(0.5)
    c.unirse(args.nombre or args.rol.capitalize(), args.rol)
    if not c.esperar(lambda c: c.jugador_id or c.error, 10):
        raise SystemExit("sin bienvenida")
    if c.error:
        json.dump({"error": c.error}, open(args.salida, "w", encoding="utf-8"))
        return
    c.enviar("listo", listo=True)
    rondas_jugadas = []
    decidida = None
    ok = c.esperar(lambda c: (c.final is not None) or c.cerrado or _jugar(c, args.politica, rng, rondas_jugadas),
                   args.limite)
    json.dump({"jugador_id": c.jugador_id, "rondas": rondas_jugadas, "final": c.final, "estado": c.estado,
               "cerrado": c.cerrado, "termino": bool(ok and c.final)}, open(args.salida, "w", encoding="utf-8"),
              ensure_ascii=False)
    c.cerrar()


def _jugar(c, politica, rng, rondas_jugadas):
    if c.ronda and c.arbol and c.ronda["ronda"] not in rondas_jugadas and not c.ya_decidi():
        rondas_jugadas.append(c.ronda["ronda"])
        if politica != "callado":
            c.decidir(elegir_ruta(c.arbol, politica, rng))
    if c.prueba and ("p", c.prueba["indice"]) not in rondas_jugadas and politica != "callado":
        rondas_jugadas.append(("p", c.prueba["indice"]))
        c.entregar_prueba(payload_bot(c.prueba, {"responsable": .75, "azar": .5}.get(politica, .3), rng))
    return False


if __name__ == "__main__":
    main()
