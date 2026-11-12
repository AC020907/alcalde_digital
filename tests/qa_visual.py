"""
Auditoria visual con el motor real. Lanza trabajos de Ren'Py en paralelo y deja capturas en una carpeta.

  recorrido: el guion real (perfil de decisiones) a velocidad de lectura, una captura por linea.
  galeria:   pantallas, menus y los cinco minijuegos jugados con entradas simuladas (game/qa_galeria.rpy).

Uso:
  python tests/qa_visual.py recorrido --perfiles investigador,casual --modo feria --salida C:/tmp/vis
  python tests/qa_visual.py galeria --tam 1920x1080,1366x768 --salida C:/tmp/vis
  python tests/qa_visual.py galeria --tam 1600x720 --movil --salida C:/tmp/vis
  python tests/qa_visual.py hojas --salida C:/tmp/vis      (hojas de contacto para revisar rapido)
"""
import argparse
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from qa_recorridos import PROYECTO, SDK_DEFECTO, GuardadoAislado  # noqa: E402

ETAPAS_GALERIA = ("menus", "personajes", "escenas", "minijuegos", "ritmo", "ritmo:nada", "ritmo:abandonar", "finales")


def lanzar(sdk, env_extra, carpeta, timeout=900):
    os.makedirs(carpeta, exist_ok=True)
    env = dict(os.environ, ALCALDE_QA_SALIDA=os.path.join(carpeta, "salida.json"), ALCALDE_SEMILLA="123",
               ALCALDE_QA_SIN_CAPTURAS="1", **env_extra)
    env.pop("CIVITAS_API", None)
    savedir = os.path.join(carpeta, "saves")
    return subprocess.Popen([os.path.join(sdk, "renpy.exe"), PROYECTO, "--savedir", savedir], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), timeout


def esperar(procesos):
    for nombre, (p, timeout) in procesos.items():
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            print("%s: tiempo agotado" % nombre)
        print("%-40s codigo %s" % (nombre, p.returncode))


def hojas(salida, por_hoja=20, ancho=384):
    from PIL import Image, ImageDraw
    for carpeta in sorted(set(os.path.dirname(f) for f in glob.glob(os.path.join(salida, "**", "*.png"), recursive=True))):
        if os.path.basename(carpeta).startswith("hoja"):
            continue
        fotos = sorted(f for f in glob.glob(os.path.join(carpeta, "*.png")) if not os.path.basename(f).startswith("hoja_"))
        for i in range(0, len(fotos), por_hoja):
            grupo = fotos[i:i + por_hoja]
            alto = None
            miniaturas = []
            for f in grupo:
                im = Image.open(f).convert("RGB")
                alto = alto or int(ancho * im.height / im.width)
                miniaturas.append((os.path.basename(f), im.resize((ancho, alto))))
            cols = 4
            filas = (len(miniaturas) + cols - 1) // cols
            hoja = Image.new("RGB", (cols * ancho, filas * (alto + 18)), "white")
            d = ImageDraw.Draw(hoja)
            for k, (nombre, im) in enumerate(miniaturas):
                x, y = (k % cols) * ancho, (k // cols) * (alto + 18)
                hoja.paste(im, (x, y + 18))
                d.text((x + 3, y + 3), nombre[:60], fill="black")
            hoja.save(os.path.join(carpeta, "hoja_%02d.jpg" % (i // por_hoja)), quality=82)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tipo", choices=("recorrido", "galeria", "arena", "hojas"))
    ap.add_argument("--sdk", default=SDK_DEFECTO)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--perfiles", default="investigador,prudente,impulsivo,casual,dividido")
    ap.add_argument("--modo", default="feria")
    ap.add_argument("--tam", default="1920x1080")
    ap.add_argument("--etapas", default=",".join(ETAPAS_GALERIA))
    ap.add_argument("--movil", action="store_true", help="variante tactil/movil de Ren'Py")
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    if args.tipo == "hojas":
        hojas(salida)
        return 0
    procesos = {}
    with GuardadoAislado():
        for tam in args.tam.split(","):
            extra = {"ALCALDE_QA_TAM": tam}
            if args.movil:
                extra["RENPY_VARIANT"] = "touch small mobile"
            sufijo = tam + ("_movil" if args.movil else "")
            if args.tipo == "arena":
                # 4 procesos independientes: Ren'Py anfitrion (ciudadano), Ren'Py cliente (periodista) y dos bots.
                for etapa in ("arena", "arena_cliente"):
                    carpeta = os.path.join(salida, "%s_%s" % (etapa, sufijo))
                    procesos[os.path.basename(carpeta)] = lanzar(args.sdk, dict(
                        extra, ALCALDE_QA="galeria", ALCALDE_QA_ETAPA=etapa, ALCALDE_QA_CAPTURAS=carpeta), carpeta)
                for rol in ("influencer", "candidato"):
                    carpeta = os.path.join(salida, "bot_%s" % rol)
                    os.makedirs(carpeta, exist_ok=True)
                    procesos["bot_" + rol] = (subprocess.Popen(
                        [sys.executable, os.path.join(PROYECTO, "tests", "arena_bot.py"), "--puerto", "50777",
                         "--rol", rol, "--salida", os.path.join(carpeta, "salida.json"), "--limite", "400"]), 500)
                continue
            if args.tipo == "recorrido":
                for perfil in args.perfiles.split(","):
                    carpeta = os.path.join(salida, "recorrido_%s_%s_%s" % (args.modo, perfil, sufijo))
                    procesos[os.path.basename(carpeta)] = lanzar(args.sdk, dict(
                        extra, ALCALDE_QA=perfil, ALCALDE_QA_MODO=args.modo, ALCALDE_QA_VISUAL=carpeta,
                        ALCALDE_QA_DURACION="420"), carpeta)
            else:
                for etapa in args.etapas.split(","):
                    # "ritmo:nada" / "ritmo:abandonar": variantes del duelo (derrota, abandono desde la pausa).
                    etapa, _, pasos = etapa.partition(":")
                    carpeta = os.path.join(salida, "galeria_%s%s_%s" % (etapa, "_" + pasos if pasos else "", sufijo))
                    procesos[os.path.basename(carpeta)] = lanzar(args.sdk, dict(
                        extra, ALCALDE_QA="galeria", ALCALDE_QA_ETAPA=etapa, ALCALDE_QA_CAPTURAS=carpeta,
                        ALCALDE_QA_PASOS=pasos or "perfecto"), carpeta)
        esperar(procesos)
    fallos = 0
    for nombre in procesos:
        f = os.path.join(salida, nombre, "salida.json")
        d = {}
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
        problema = verificar(nombre, d)
        fallos += bool(problema)
        resumen = d.get("final") or {k: v for k, v in d.get("galeria", {}).items() if k in ("eventos", "historial")}
        print("%-40s %-6s %s %s" % (nombre, "FALLO" if problema else "OK", problema or "", resumen))
    hojas(salida)
    return 1 if fallos else 0


ESPERADO_RECORRIDO = {"investigador": "secreto", "prudente": "informada", "impulsivo": "mandato",
                      "casual": "caos", "dividido": "dividida"}


def verificar(nombre, d):
    """Regresiones de la auditoria final: cada etapa debe terminar sola y con el resultado esperado."""
    if not d:
        return "sin salida (bloqueo o cierre)"
    if d.get("error") or d.get("vigilante") or d.get("vigilante_hilo"):
        return "error/bloqueo: %s" % (d.get("error") or d.get("vigilante") or d.get("vigilante_hilo"))
    if nombre.startswith("recorrido_"):
        perfil = nombre.split("_")[2]
        return None if d.get("final") == ESPERADO_RECORRIDO.get(perfil) else "final %s" % d.get("final")
    if nombre.startswith("bot_"):
        return None if d.get("termino") else "el bot no llego al final: %s" % d.get("cerrado")
    g = d.get("galeria", {})
    if g.get("etapa") == "arena_solo":
        return None
    if g.get("etapa") == "arena":
        finales = [e for e in g.get("eventos", []) if e[0] == "final"]
        return None if finales else "la Arena no llego a la eleccion"

    if not g.get("ok"):
        return "la etapa no termino"
    eventos = g.get("eventos", [])
    if g.get("etapa") == "minijuegos" and [e[0] for e in eventos if e[0] != "plataformas_fps"] != ["moderador", "contencion", "viralizacion", "rastreador"]:
        return "algun minijuego no devolvio el control: %s" % eventos
    if g.get("etapa") == "ritmo":
        # Perfecto (con pausa y reanudacion) debe ganar; sin pulsar o abandonando, perder.
        exito = eventos and eventos[0][1]
        if ("_nada_" in nombre or "_abandonar_" in nombre) == bool(exito):
            return "resultado del duelo inesperado: %s" % eventos
    if g.get("etapa") in ("menus", "dialogo") and not g.get("historial"):
        return "el historial no registro las lineas"
    return None


if __name__ == "__main__":
    sys.exit(main())
