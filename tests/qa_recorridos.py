"""
Recorridos automaticos del guion real dentro de Ren'Py (game/qa_autoplay.rpy).
Cada perfil de jugador debe llegar a su final esperado, en historia y en Modo Feria.

Uso:  python tests/qa_recorridos.py [--sdk RUTA_SDK] [--api URL_LEADERBOARD]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SDK_DEFECTO = os.path.expanduser(r"~\Downloads\renpy-8.5.3-sdk")

ESPERADO = {
    "investigador": "secreto",
    "prudente": "informada",
    "impulsivo": "mandato",
    "casual": "caos",
    "dividido": "dividida",
}


def recorrer(sdk, perfil, modo, salida, api=None, semilla="123"):
    env = dict(os.environ, ALCALDE_QA=perfil, ALCALDE_QA_MODO=modo, ALCALDE_QA_SALIDA=salida,
               ALCALDE_SEMILLA=semilla,
               # Duracion plausible para el validador del servidor (el recorrido real dura ~2 s).
               ALCALDE_QA_DURACION="1500" if modo == "historia" else "420")
    if api:
        env["CIVITAS_API"] = api
    if os.path.exists(salida):
        os.remove(salida)
    inicio = time.time()
    # --savedir aislado: los recorridos no tocan el progreso real (Archivo de Destinos, alias, cola).
    savedir = os.path.join(os.path.dirname(salida), "saves")
    subprocess.run([os.path.join(sdk, "renpy.exe"), PROYECTO, "--savedir", savedir], env=env, timeout=300,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    duracion = time.time() - inicio
    if not os.path.exists(salida):
        return {"error": "sin salida (el juego no llego a la pantalla de resultados)"}, duracion
    with open(salida, encoding="utf-8") as f:
        return json.load(f), duracion


class GuardadoAislado:
    """Ren'Py tambien guarda en game/saves al arrancar: se aparta durante QA y se restaura siempre."""

    def __init__(self):
        self.real = os.path.join(PROYECTO, "game", "saves")
        self.aparte = self.real + ".qa_aparte"

    def __enter__(self):
        if os.path.exists(self.aparte):
            raise RuntimeError("Quedo %s de una ejecucion anterior: revisalo antes de seguir." % self.aparte)
        if os.path.isdir(self.real):
            os.rename(self.real, self.aparte)
        return self

    def __exit__(self, *exc):
        if os.path.isdir(self.aparte):
            if os.path.isdir(self.real):
                shutil.rmtree(self.real)  # lo creo QA
            os.rename(self.aparte, self.real)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdk", default=SDK_DEFECTO)
    ap.add_argument("--api", default=None)
    ap.add_argument("--semilla", default="123")
    args = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="civitas_qa_")
    print("%-13s %-9s %-10s %-10s %6s  %-8s %s" % ("perfil", "modo", "esperado", "obtenido", "puntos", "seg", "nota"))
    with GuardadoAislado():
        fallos = recorrer_todo(args, tmp)
    print("\n%d fallos. Detalle JSON en %s" % (fallos, tmp))
    return 1 if fallos else 0


def recorrer_todo(args, tmp):
    fallos = 0
    for modo in ("historia", "feria"):
        for perfil, esperado in ESPERADO.items():
            datos, seg = recorrer(args.sdk, perfil, modo, os.path.join(tmp, "%s_%s.json" % (perfil, modo)),
                                  args.api, args.semilla)
            obtenido = datos.get("final")
            ok = obtenido == esperado and not datos.get("error")
            fallos += not ok
            nota = datos.get("error") or ("envio: %s" % (datos.get("estado_envio") or ["-"])[0])
            total = (datos.get("resultado") or {}).get("total", "-")
            print("%-13s %-9s %-10s %-10s %6s  %-8.1f %s %s" % (perfil, modo, esperado, obtenido, total, seg,
                                                               "OK " if ok else "FALLO", nota))
    return fallos


if __name__ == "__main__":
    sys.exit(main())
