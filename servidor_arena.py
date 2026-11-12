"""
Servidor dedicado de la Arena Civitas para la red local (no necesita internet, Render ni Neon).

    python servidor_arena.py                      # puerto 50777, 5 rondas de 25 s
    python servidor_arena.py --rondas 3 --segundos 20 --semilla 7

Los jugadores abren el juego, eligen "Arena (2-4 jugadores)" -> "Unirse" y escriben la IP que se
muestra abajo. Sin clave de anfitrion, el primero en unirse es el anfitrion (pulsa "Empezar").
Ctrl+C para cerrar.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "game"))

from clases.arena import protocolo  # noqa: E402
from clases.arena.servidor import ServidorArena  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--puerto", type=int, default=protocolo.PUERTO)
    ap.add_argument("--rondas", type=int, default=5)
    ap.add_argument("--segundos", type=int, default=25)
    ap.add_argument("--semilla", type=int, default=None, help="misma semilla = misma partida (demos y pruebas)")
    args = ap.parse_args()
    srv = ServidorArena(puerto=args.puerto, semilla=args.semilla, rondas=args.rondas, segundos=args.segundos)
    srv.iniciar()
    print("Arena Civitas escuchando en el puerto %d (semilla %s)." % (srv.puerto, srv.semilla))
    print("IP para unirse: %s" % ", ".join(srv.direcciones_lan()))
    vistos = 0
    try:
        while True:
            time.sleep(0.5)
            with srv.lock:
                nuevos = srv.registro[vistos:]
                vistos = len(srv.registro)
            for evento in nuevos:
                print("  " + " ".join(str(x) for x in evento))
    except KeyboardInterrupt:
        print("Cerrando la sala.")
        srv.detener()


if __name__ == "__main__":
    main()
