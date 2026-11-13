"""Copia el arte v2 del plataformero a la Arena Online (WebP, mas ligero para telefonos).

    python tools/arte/plataformas_arte.py          # genera game/gui/plataformas/v2/*.png
    python tools/arte/exportar_plataformas_web.py  # -> leaderboard/app/static/plataformas/v2/*.webp
"""
import os

from PIL import Image

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ORIGEN = os.path.join(RAIZ, "game", "gui", "plataformas", "v2")
DESTINO = os.path.join(RAIZ, "leaderboard", "app", "static", "plataformas", "v2")


def main():
    os.makedirs(DESTINO, exist_ok=True)
    total = 0
    for nombre in sorted(os.listdir(ORIGEN)):
        if not nombre.endswith(".png"):
            continue
        im = Image.open(os.path.join(ORIGEN, nombre)).convert("RGBA")
        if nombre.startswith(("fondo_", "primer_plano")):
            im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)      # el canvas web es mas pequeno
            calidad = 72
        else:
            calidad = 88
        ruta = os.path.join(DESTINO, nombre[:-4] + ".webp")
        im.save(ruta, "WEBP", quality=calidad, method=6)
        total += os.path.getsize(ruta)
    print("ok: %d archivos, %.0f KB en %s" % (len(os.listdir(DESTINO)), total / 1024.0, DESTINO))


if __name__ == "__main__":
    main()
