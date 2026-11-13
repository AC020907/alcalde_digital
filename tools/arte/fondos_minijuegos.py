"""Fondos de Caza-Rumores, Rastreador y Gran Viralizacion (remaster): el mapa ilustrado de Ciudad Nova
entintado y apagado, para que el grafo se lea sobre la ciudad real (misma idea que la apertura).
Los originales quedan en tools/arte/respaldo_v1/.   python tools/arte/fondos_minijuegos.py"""
import os
from PIL import Image, ImageFilter, ImageOps

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MAPA = os.path.join(RAIZ, "game", "images", "bg", "mapa.jpg")
DEST = os.path.join(RAIZ, "game", "assets", "backgrounds")
TONOS = {"fondo_contencion.jpg": ((16, 11, 26), (92, 58, 84)),      # rojo apagado: crisis
         "fondo_rastreador.jpg": ((14, 12, 28), (70, 74, 112)),     # lila y azul: investigacion
         "fondo_viralizacion.jpg": ((18, 10, 22), (104, 46, 72))}   # vino: la gran viralizacion

base = Image.open(MAPA).convert("L").resize((1920, 1280), Image.LANCZOS).crop((0, 100, 1920, 1180))
base = ImageOps.autocontrast(base, cutoff=2).filter(ImageFilter.GaussianBlur(1.4))
for nombre, (oscuro, claro) in TONOS.items():
    im = ImageOps.colorize(base, black=oscuro, white=claro)
    velo = Image.new("RGB", im.size, oscuro)
    im = Image.blend(im, velo, 0.35)
    im.save(os.path.join(DEST, nombre), quality=86)
print("ok")
