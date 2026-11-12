"""
Importa los sprites oficiales de los personajes (sprites.zip del equipo) al juego.

    python tools/arte/importar_sprites.py <carpeta_extraida_del_zip>

Qué hace (y por qué):
- Solo usa los PNG. Los .kra (Krita) son archivos de trabajo y no se copian al juego.
- Normaliza los nombres al esquema del juego: <personaje>_<expresion>.png con expresiones en femenino
  (neutral, feliz, seria, enojada, triste, sorprendida). Rodrigo viene en masculino (enojado, serio...).
- Encuadre comun por personaje: todas las expresiones se recortan con la UNION de sus cajas y se escalan igual,
  asi cambiar de expresion no mueve la figura. Las expresiones entregadas a 570 px se llevan primero al lienzo
  de 2480 px (mismo encuadre que las de 2480, comprobado) y luego se reducen como las demas; quedan algo
  mas suaves, no se inventa detalle.
- Duplicados de contenido identico (Claudia seria = neutral, Rodrigo serio = neutral): se guarda un solo
  archivo y la expresion repetida queda como alias en ALIAS_EXPRESION (personajes.rpy). Sin copias.
- Expresiones que faltan en el ZIP: NOVA no trae "feliz"; se usa su "neutral" (guino y sonrisa) como alias.
  No se genera arte nuevo.
- Regenera los retratos laterales (lado/<p>_<e>_lado.png, 230 px, circulo con aro del color del personaje).
- Tomas llego aparte (tomas_sprites.zip, 1254 px): se importa igual, con su carpeta tomas/.
- Alfa casi opaco (>= 200) se lleva a 255: los PNG generados traen la figura a alfa 253.

Escribe en game/images/personajes/sprites/ y imprime un informe (tamanos, alias, duplicados).
"""
import hashlib
import os
import sys

from PIL import Image, ImageDraw

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DESTINO = os.path.join(RAIZ, "game", "images", "personajes", "sprites")
LADO = os.path.join(DESTINO, "lado")
EXPRESIONES = ("neutral", "feliz", "seria", "enojada", "triste", "sorprendida")
MASCULINO = {"serio": "seria", "enojado": "enojada", "sorprendido": "sorprendida"}
LIENZO = 2480
ALTO_SALIDA = 760                     # alto del sprite en el juego (se muestra a zoom 1.0)
COLOR = {"claudia": ("#5b5bd6", "#dcdcfa"), "martina": ("#d6457a", "#f8d6e3"), "rodrigo": ("#2f9e8f", "#cdeee9"),
         "nova": ("#3b4cc0", "#d9ddf7"), "tomas": ("#c99a2e", "#f6ecd2")}
# Cara para el retrato lateral: (centro x, centro y, lado) en fraccion del recorte del personaje.
CARA = {"claudia": (0.50, 0.30, 0.52), "martina": (0.50, 0.30, 0.46), "rodrigo": (0.50, 0.28, 0.46), "nova": (0.50, 0.24, 0.50), "tomas": (0.50, 0.30, 0.46)}
ALIAS_FALTANTE = {("nova", "feliz"): "neutral"}


def cargar(carpeta):
    """{personaje: {expresion: Image}} con nombres normalizados y todo llevado al lienzo de 2480 px."""
    datos = {}
    for personaje in sorted(os.listdir(carpeta)):
        dirp = os.path.join(carpeta, personaje)
        if not os.path.isdir(dirp):
            continue
        for archivo in sorted(os.listdir(dirp)):
            base, ext = os.path.splitext(archivo)
            if ext.lower() != ".png":
                continue
            p, _, expr = base.partition("_")
            expr = MASCULINO.get(expr, expr)
            if p != personaje or expr not in EXPRESIONES:
                print("  ignorado (nombre inesperado):", archivo)
                continue
            im = Image.open(os.path.join(dirp, archivo)).convert("RGBA")
            if im.size != (LIENZO, LIENZO):
                im = im.resize((LIENZO, LIENZO), Image.LANCZOS)
            r, g, b, a = im.split()
            im = Image.merge("RGBA", (r, g, b, a.point(lambda v: 255 if v >= 200 else v)))
            datos.setdefault(personaje, {})[expr] = im
    return datos


def huella(im):
    return hashlib.sha1(im.tobytes()).hexdigest()


def retrato_lado(img, personaje):
    cx, cy, lado = CARA[personaje]
    w, h = img.size
    s = int(lado * h)
    x0, y0 = int(cx * w - s / 2), int(cy * h - s / 2)
    cara = img.crop((x0, y0, x0 + s, y0 + s)).resize((214, 214), Image.LANCZOS)
    aro, fondo = COLOR[personaje]
    out = Image.new("RGBA", (230, 230), (0, 0, 0, 0))
    disco = Image.new("RGBA", (214, 214), fondo)
    disco.alpha_composite(cara)
    mascara = Image.new("L", (214, 214), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, 213, 213), fill=255)
    out.paste(disco, (8, 8), mascara)
    d = ImageDraw.Draw(out)
    d.ellipse((3, 3, 226, 226), outline="#ffffff", width=4)
    d.ellipse((7, 7, 222, 222), outline=aro, width=3)
    return out


def main(carpeta):
    datos = cargar(carpeta)
    os.makedirs(LADO, exist_ok=True)
    alias, informe = {}, []
    for personaje, exprs in datos.items():
        cajas = [im.getbbox() for im in exprs.values()]
        union = (min(c[0] for c in cajas), min(c[1] for c in cajas), max(c[2] for c in cajas), max(c[3] for c in cajas))
        margen = 12
        recorte = (max(0, union[0] - margen), max(0, union[1] - margen), min(LIENZO, union[2] + margen), LIENZO)
        escala = ALTO_SALIDA / float(recorte[3] - recorte[1])
        tam = (int(round((recorte[2] - recorte[0]) * escala)), ALTO_SALIDA)
        vistos = {}
        for expr in EXPRESIONES:
            if expr not in exprs:
                continue
            h = huella(exprs[expr])
            if h in vistos:                          # contenido identico: alias, no se duplica el archivo
                alias[(personaje, expr)] = vistos[h]
                for f in (os.path.join(DESTINO, "%s_%s.png" % (personaje, expr)), os.path.join(LADO, "%s_%s_lado.png" % (personaje, expr))):
                    if os.path.exists(f):
                        os.remove(f)
                continue
            vistos[h] = expr
            img = exprs[expr].crop(recorte).resize(tam, Image.LANCZOS)
            img.save(os.path.join(DESTINO, "%s_%s.png" % (personaje, expr)), optimize=True)
            retrato_lado(img, personaje).save(os.path.join(LADO, "%s_%s_lado.png" % (personaje, expr)), optimize=True)
        for expr in EXPRESIONES:
            if expr not in exprs and (personaje, expr) in ALIAS_FALTANTE:
                alias[(personaje, expr)] = ALIAS_FALTANTE[(personaje, expr)]
                for f in (os.path.join(DESTINO, "%s_%s.png" % (personaje, expr)), os.path.join(LADO, "%s_%s_lado.png" % (personaje, expr))):
                    if os.path.exists(f):
                        os.remove(f)
            elif expr not in exprs:
                print("  FALTA %s %s (sin alias definido)" % (personaje, expr))
        informe.append("%s: %d expresiones, lienzo %dx%d" % (personaje, len(vistos), tam[0], tam[1]))
    print("\n".join(informe))
    print("Alias:", {"%s_%s" % k: v for k, v in sorted(alias.items())})
    return alias


if __name__ == "__main__":
    main(sys.argv[1])
