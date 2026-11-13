"""Inventario verificable para la remasterizacion visual.

    python tools/remaster/inventario.py guardar docs/remaster/inventario_antes.json
    python tools/remaster/inventario.py comparar docs/remaster/inventario_antes.json

- Arte oficial: SHA-256 de cada archivo bajo game/images/personajes (sprites, laterales, bases).
- Narrativa: cada label, cada linea de dialogo (personaje + texto), cada opcion de menu, cada condicion de
  opcion y cada llamada/salto entre labels, en el orden en que aparecen en cada archivo .rpy de la historia.
  La presentacion (show/scene/with/at/camera/transforms/pantallas) NO se inventaria: es lo que se remasteriza.
"""
import hashlib
import json
import os
import re
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GAME = os.path.join(RAIZ, "game")
CARPETAS_HISTORIA = ("story", "minijuegos", "arena")
EXCLUIR = ("qa_", "apertura.rpy")   # la apertura ya se inventario en su propia rama; QA no es historia

DIALOGO = re.compile(r'^\s*(?:(\w+)\s+)?(?:(?:\w+\s+)*?)"((?:[^"\\]|\\.)*)"\s*(?:with\s+\w+)?\s*$')
OPCION = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*(if\s+.+)?:\s*$')
LABEL = re.compile(r"^\s*label\s+([\w.]+)")
SALTO = re.compile(r"^\s*(call|jump)\s+([\w.]+)")
PRESENTACION = ("show ", "scene ", "hide ", "with ", "camera", "window ", "play ", "stop ", "queue ",
                "pause", "voice ", "$ ", "python", "init", "define", "default", "transform", "screen",
                "image ", "style", "#", "menu", "if ", "elif ", "else", "while ", "return", "pass")


def arte():
    out = {}
    base = os.path.join(GAME, "images", "personajes")
    for raiz, _d, archivos in os.walk(base):
        for a in sorted(archivos):
            ruta = os.path.join(raiz, a)
            with open(ruta, "rb") as f:
                out[os.path.relpath(ruta, RAIZ).replace("\\", "/")] = hashlib.sha256(f.read()).hexdigest()
    return out


def narrativa():
    out = {}
    for carpeta in CARPETAS_HISTORIA:
        dirp = os.path.join(GAME, carpeta)
        for a in sorted(os.listdir(dirp)):
            if not a.endswith(".rpy") or a.startswith(EXCLUIR) or a in EXCLUIR:
                continue
            items = []
            en_screen = False
            with open(os.path.join(dirp, a), encoding="utf-8") as f:
                for linea in f:
                    sin = linea.rstrip("\n")
                    if re.match(r"^(screen|init|transform|style)\b", sin):
                        en_screen = True
                    elif re.match(r"^label\b", sin):
                        en_screen = False
                    if en_screen:
                        continue
                    m = LABEL.match(sin)
                    if m:
                        items.append(["label", m.group(1)])
                        continue
                    m = SALTO.match(sin)
                    if m and m.group(2) == "screen":
                        continue          # mostrar una pantalla es presentacion, no un evento narrativo
                    if m:
                        items.append([m.group(1), m.group(2)])
                        continue
                    m = OPCION.match(sin)
                    if m:
                        items.append(["opcion", m.group(1), (m.group(2) or "").strip()])
                        continue
                    st = sin.strip()
                    if not st or st.startswith(PRESENTACION):
                        continue
                    m = DIALOGO.match(sin)
                    if m:
                        items.append(["dice", m.group(1) or "", m.group(2)])
            out[carpeta + "/" + a] = items
    return out


def guardar(ruta):
    datos = {"arte": arte(), "narrativa": narrativa()}
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    n = sum(len(v) for v in datos["narrativa"].values())
    print("arte: %d archivos | narrativa: %d elementos en %d archivos" % (len(datos["arte"]), n, len(datos["narrativa"])))


def comparar(ruta):
    with open(ruta, encoding="utf-8") as f:
        antes = json.load(f)
    ahora = {"arte": arte(), "narrativa": narrativa()}
    fallos = 0
    for k, h in antes["arte"].items():
        if ahora["arte"].get(k) != h:
            print("ARTE CAMBIADO O FALTA:", k)
            fallos += 1
    for k in ahora["arte"]:
        if k not in antes["arte"]:
            print("ARTE NUEVO (no permitido sin autorizacion):", k)
            fallos += 1
    for archivo, items in antes["narrativa"].items():
        if ahora["narrativa"].get(archivo) != items:
            fallos += 1
            nuevos = ahora["narrativa"].get(archivo, [])
            print("NARRATIVA DISTINTA:", archivo, "(%d -> %d elementos)" % (len(items), len(nuevos)))
            for i, (a, b) in enumerate(zip(items, nuevos)):
                if a != b:
                    print("   primer cambio en", i, a, "->", b)
                    break
    for archivo in ahora["narrativa"]:
        if archivo not in antes["narrativa"] and ahora["narrativa"][archivo]:
            print("ARCHIVO NARRATIVO NUEVO:", archivo, len(ahora["narrativa"][archivo]))
    total = sum(len(v) for v in antes["narrativa"].values())
    print("Comparados %d archivos de arte y %d elementos narrativos: %s" % (
        len(antes["arte"]), total, "IDENTICOS" if not fallos else "%d DIFERENCIAS" % fallos))
    return fallos


if __name__ == "__main__":
    accion, ruta = sys.argv[1], sys.argv[2]
    sys.exit(guardar(ruta) if accion == "guardar" else (1 if comparar(ruta) else 0))
