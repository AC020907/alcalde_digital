"""
Copia al servidor online los recursos ORIGINALES del Duelo de Frecuencias (una sola fuente: game/).

- Audio: OGG -> AAC (.m4a), porque Safari en iPhone/iPad no decodifica Vorbis. Se sirven los dos y el
  navegador usa el que pueda decodificar. Requiere `pip install imageio-ffmpeg` solo al regenerar.
- Notas y receptores: los mismos PNG del juego.
- NOVA: los sprites del juego reducidos (el telefono no necesita 1500 px).

Los charts NO se copian: el servidor los lee de game/ritmo/ (mismo archivo que Ren'Py).

Uso:  python tools/web/exportar_ritmo_online.py
"""
import os
import shutil
import subprocess

from PIL import Image

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DESTINO = os.path.join(RAIZ, "leaderboard", "app", "static", "ritmo")
MUSICA = os.path.join(RAIZ, "game", "assets", "audio", "music")
GUI = os.path.join(RAIZ, "game", "gui", "ritmo")
SPRITES = os.path.join(RAIZ, "game", "images", "personajes", "sprites")
EXPRESIONES_NOVA = ("seria", "feliz", "enojada")
# Mismos alias que game/story/personajes.rpy (ALIAS_EXPRESION): expresiones identicas o que faltan.
ALIAS = {("claudia", "seria"): "neutral", ("rodrigo", "seria"): "neutral", ("nova", "feliz"): "neutral"}


def sprite(personaje, expresion):
    return os.path.join(SPRITES, "%s_%s.png" % (personaje, ALIAS.get((personaje, expresion), expresion)))


def main():
    os.makedirs(DESTINO, exist_ok=True)
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    for modo in ("feria", "historia"):
        origen = os.path.join(MUSICA, "duelo_%s.ogg" % modo)
        shutil.copyfile(origen, os.path.join(DESTINO, "duelo_%s.ogg" % modo))
        subprocess.check_call([ff, "-loglevel", "error", "-y", "-i", origen, "-c:a", "aac", "-b:a", "128k",
                               os.path.join(DESTINO, "duelo_%s.m4a" % modo)])
    for k in range(4):
        for nombre in ("nota_%d.png", "receptor_%d.png", "receptor_on_%d.png"):
            shutil.copyfile(os.path.join(GUI, nombre % k), os.path.join(DESTINO, nombre % k))
    for e in EXPRESIONES_NOVA:
        img = Image.open(sprite("nova", e)).convert("RGBA")
        img.thumbnail((520, 520))
        img.save(os.path.join(DESTINO, "nova_%s.webp" % e), quality=85)
    print("Recursos exportados en", DESTINO)


def exportar_arena():
    """Retratos y fondos del juego para la Arena Online narrativa (misma identidad visual que la novela)."""
    destino = os.path.join(RAIZ, "leaderboard", "app", "static", "arena")
    os.makedirs(destino, exist_ok=True)
    for personaje in ("claudia", "martina", "rodrigo", "tomas", "nova"):
        for expresion in ("seria", "feliz"):
            img = Image.open(sprite(personaje, expresion)).convert("RGBA")
            caja = img.getbbox()
            img = img.crop(caja)
            img = img.crop((0, 0, img.width, min(img.height, int(img.width * 1.25))))      # busto
            img.thumbnail((420, 520))
            img.save(os.path.join(destino, "%s_%s.webp" % (personaje, expresion)), quality=86)
    fondos = {"operaciones": None, "viral": os.path.join(RAIZ, "game", "assets", "backgrounds", "fondo_viralizacion.jpg"),
              "red": os.path.join(RAIZ, "game", "assets", "backgrounds", "fondo_contencion.jpg"),
              "evidencias": os.path.join(RAIZ, "game", "assets", "backgrounds", "fondo_rastreador.jpg")}
    for carpeta, _d, archivos in os.walk(os.path.join(RAIZ, "game")):
        for a in archivos:
            if a.lower().startswith("operaciones") and a.lower().endswith((".jpg", ".png", ".webp")):
                fondos["operaciones"] = os.path.join(carpeta, a)
    for nombre, ruta in fondos.items():
        if ruta and os.path.exists(ruta):
            img = Image.open(ruta).convert("RGB")
            img.thumbnail((1280, 720))
            img.save(os.path.join(destino, "fondo_%s.webp" % nombre), quality=72)
    print("Arena:", sorted(os.listdir(destino)))


if __name__ == "__main__":
    main()
    exportar_arena()
