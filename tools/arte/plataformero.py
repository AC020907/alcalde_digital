"""
Genera el arte ORIGINAL del plataformero «Ruta de la Verdad» (sprites, tiles y fondos) con dibujo vectorial
sencillo en PIL. Nada procede de otros juegos. Estilo: personaje calido/pastel (crema, vino, violeta, coral)
dentro del sistema oscuro y neon de NOVA.

Salida: game/gui/plataformas/*.png  y copia para la web en leaderboard/app/static/plataformas/
Uso:    python tools/arte/plataformero.py
"""
import math
import os
import shutil

from PIL import Image, ImageDraw, ImageFilter

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(RAIZ, "game", "gui", "plataformas")
WEB = os.path.join(RAIZ, "leaderboard", "app", "static", "plataformas")
S = 4            # supermuestreo
CREMA, VINO, VIOLETA, CORAL, PIEL, OSCURO = "#fbf1dc", "#8c2f4b", "#6d5bd0", "#f2816b", "#f3c9a5", "#2b2440"
NEON, NEON2, FONDO = "#5eead4", "#f0abfc", "#0d0a1a"


def lienzo(w, h):
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def guardar(img, nombre, w, h):
    img.resize((w, h), Image.LANCZOS).save(os.path.join(OUT, nombre + ".png"))


def R(d, x0, y0, x1, y1, r, **kw):
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, **kw)


def E(d, x0, y0, x1, y1, **kw):
    d.ellipse([x0 * S, y0 * S, x1 * S, y1 * S], **kw)


def jugador(nombre, pierna_a=0.0, pierna_b=0.0, brazo=0.0, dy=0, ojos="normal", bufanda=0.0, tinte=None):
    """Mensajero de Civitas: capucha crema, bufanda vino, cuerpo violeta. 56x64 px."""
    W, H = 56, 64
    img, d = lienzo(W, H)
    cx, base = 28, 60 + dy
    for ang, col in ((pierna_a, OSCURO), (pierna_b, "#3a3158")):          # piernas
        x = cx + math.sin(ang) * 9
        y = base - 4 - abs(math.cos(ang)) * 2 + (0 if abs(ang) < 1.2 else -6)
        R(d, x - 4.5, base - 18, x + 4.5, y + 4, 4, fill=col)
        R(d, x - 6, y, x + 7, y + 6, 3, fill=VINO)                         # zapato
    R(d, cx - 12, base - 40, cx + 12, base - 14, 9, fill=VIOLETA)          # cuerpo
    R(d, cx - 12, base - 26, cx + 12, base - 14, 6, fill="#5a49b8")
    bx = cx + 10 + math.sin(brazo) * 6                                     # brazo delantero
    R(d, bx - 3.5, base - 36 + math.cos(brazo) * 2, bx + 4, base - 20 - math.sin(brazo) * 6, 3.5, fill=VIOLETA)
    E(d, bx - 3, base - 23 - math.sin(brazo) * 6, bx + 5, base - 15 - math.sin(brazo) * 6, fill=PIEL)
    # bufanda al viento
    d.polygon([((cx - 10) * S, (base - 40) * S), ((cx - 26 - bufanda * 6) * S, (base - 44 - bufanda * 5) * S),
               ((cx - 24 - bufanda * 6) * S, (base - 34 - bufanda * 2) * S), ((cx - 10) * S, (base - 33) * S)], fill=VINO)
    R(d, cx - 13, base - 43, cx + 13, base - 35, 4, fill=VINO)
    E(d, cx - 15, base - 66, cx + 15, base - 38, fill=CREMA)               # capucha
    E(d, cx - 9, base - 59, cx + 13, base - 40, fill=PIEL)                 # cara
    if ojos == "dano":
        for ox in (cx + 1, cx + 8):
            d.line([(ox - 2) * S, (base - 53) * S, (ox + 2) * S, (base - 49) * S], fill=OSCURO, width=S * 2)
            d.line([(ox - 2) * S, (base - 49) * S, (ox + 2) * S, (base - 53) * S], fill=OSCURO, width=S * 2)
    else:
        alto = 5 if ojos == "normal" else 6.5
        for ox in (cx + 1, cx + 8):
            E(d, ox - 1.8, base - 53, ox + 1.8, base - 53 + alto, fill=OSCURO)
        E(d, cx + 10, base - 47, cx + 14, base - 44, fill=CORAL + "aa")
    if tinte:
        capa = Image.new("RGBA", img.size, tinte)
        img = Image.composite(capa, img, img.split()[3].point(lambda a: 110 if a else 0)) if False else Image.alpha_composite(
            img, Image.composite(capa, Image.new("RGBA", img.size, (0, 0, 0, 0)), img.split()[3]))
    guardar(img, nombre, W, H)


def tiles():
    T = 48
    img, d = lienzo(T, T)                                                  # suelo: panel del sistema de NOVA
    R(d, 0, 0, T, T, 0, fill="#181230")
    R(d, 1, 1, T - 1, T - 1, 5, fill="#221a42", outline="#3b2f6b", width=S)
    d.line([4 * S, 3 * S, (T - 4) * S, 3 * S], fill=NEON, width=S * 2)
    for x, y in ((10, 16), (30, 26), (18, 36)):
        R(d, x, y, x + 12, y + 3, 1.5, fill="#34295e")
    guardar(img, "suelo", T, T)
    img, d = lienzo(T, T)                                                  # relleno bajo el suelo
    R(d, 0, 0, T, T, 0, fill="#130e26")
    for x, y in ((8, 10), (28, 30)):
        R(d, x, y, x + 10, y + 3, 1.5, fill="#1f1838")
    guardar(img, "relleno", T, T)
    img, d = lienzo(T, T)                                                  # pinchos: interferencia de NOVA
    for k in range(4):
        x = 2 + k * 11.5
        d.polygon([(x * S, T * S), ((x + 5) * S, 10 * S), ((x + 10) * S, T * S)], fill="#e11d74")
        d.polygon([((x + 3) * S, T * S), ((x + 5) * S, 22 * S), ((x + 7) * S, T * S)], fill="#ff8fc7")
    guardar(img, "pincho", T, T)
    for nombre, alfa, borde in (("bloque_on", 255, NEON2), ("bloque_aviso", 150, "#fde68a"), ("bloque_off", 40, "#6b5b95")):
        img, d = lienzo(T, T)
        R(d, 2, 2, T - 2, T - 2, 7, fill=(80, 40, 120, alfa), outline=borde, width=S * 2)
        if alfa > 60:
            d.line([10 * S, 24 * S, 38 * S, 24 * S], fill=borde, width=S * 2)
        guardar(img, nombre, T, T)
    img, d = lienzo(T, T)                                                  # evidencia: documento luminoso
    brillo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    db = ImageDraw.Draw(brillo)
    E(db, 4, 4, 44, 44, fill=(250, 204, 21, 90))
    img = Image.alpha_composite(img, brillo.filter(ImageFilter.GaussianBlur(5 * S)))
    d = ImageDraw.Draw(img)
    R(d, 13, 8, 35, 40, 3, fill=CREMA, outline="#c58a1b", width=S)
    d.polygon([(28 * S, 8 * S), (35 * S, 15 * S), (28 * S, 15 * S)], fill="#e9d8a6")
    for y in (20, 25, 30):
        d.line([17 * S, y * S, 31 * S, y * S], fill=VINO, width=S * 2)
    E(d, 26, 29, 36, 39, fill="#facc15", outline="#c58a1b", width=S)
    guardar(img, "evidencia", T, T)
    for nombre, col in (("control_off", "#6b5b95"), ("control_on", NEON)):   # punto de control: antena
        img, d = lienzo(T, T)
        R(d, 21, 14, 27, T, 2, fill="#3b2f6b")
        E(d, 15, 4, 33, 22, fill=col, outline="#ffffff", width=S)
        R(d, 12, T - 6, 36, T, 2, fill="#3b2f6b")
        guardar(img, nombre, T, T)
    img, d = lienzo(72, 96)                                                # meta: archivo original (portal)
    brillo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    E(ImageDraw.Draw(brillo), 4, 8, 68, 92, fill=(94, 234, 212, 110))
    img = Image.alpha_composite(img, brillo.filter(ImageFilter.GaussianBlur(7 * S)))
    d = ImageDraw.Draw(img)
    R(d, 14, 14, 58, 94, 10, fill="#102a2a", outline=NEON, width=S * 2)
    R(d, 24, 30, 48, 62, 3, fill=CREMA)
    for y in (38, 44, 50):
        d.line([28 * S, y * S, 44 * S, y * S], fill=VINO, width=S * 2)
    d.polygon([(30 * S, 74 * S), (42 * S, 74 * S), (36 * S, 84 * S)], fill=NEON)
    guardar(img, "meta", 72, 96)


def fondos():
    for nombre, w, h, col, n, semilla in (("fondo_lejos", 960, 540, "#1b1440", 26, 3), ("fondo_cerca", 960, 540, "#2a1f5c", 16, 9)):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = 0
        rnd = __import__("random").Random(semilla)
        while x < w:                                                       # torres de servidores de NOVA
            aw, ah = rnd.randint(30, 80), rnd.randint(120, 360) if nombre == "fondo_lejos" else rnd.randint(60, 220)
            d.rectangle([x, h - ah, x + aw, h], fill=col)
            for k in range(rnd.randint(2, 7)):
                yy = h - ah + 12 + k * 22
                if yy < h - 10:
                    d.rectangle([x + 6, yy, x + aw - 6, yy + 3], fill=rnd.choice(("#5eead455", "#f0abfc44", "#ffffff18")))
            x += aw + rnd.randint(8, 40)
        img.save(os.path.join(OUT, nombre + ".png"))
    cielo = Image.new("RGB", (64, 540))
    d = ImageDraw.Draw(cielo)
    for y in range(540):
        t = y / 539.0
        d.line([0, y, 64, y], fill=(int(13 + 22 * t), int(10 + 8 * t), int(26 + 40 * t)))
    cielo.save(os.path.join(OUT, "cielo.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    jugador("idle_0")
    jugador("idle_1", dy=1, bufanda=0.3)
    for k in range(4):
        a = k / 4.0 * 2 * math.pi
        jugador("corre_%d" % k, pierna_a=math.sin(a) * 0.9, pierna_b=-math.sin(a) * 0.9, brazo=-math.sin(a), dy=-abs(math.sin(a)) * 2, bufanda=1.0)
    jugador("salto", pierna_a=0.5, pierna_b=-0.7, brazo=1.2, ojos="abiertos", bufanda=0.6)
    jugador("cae", pierna_a=-0.3, pierna_b=0.6, brazo=-1.2, ojos="abiertos", bufanda=-0.8)
    jugador("dano", pierna_a=0.8, pierna_b=-0.8, brazo=1.4, ojos="dano", tinte=(244, 63, 94, 110))
    tiles()
    fondos()
    os.makedirs(WEB, exist_ok=True)
    for f in os.listdir(OUT):
        shutil.copyfile(os.path.join(OUT, f), os.path.join(WEB, f))
    print("Arte del plataformero:", len(os.listdir(OUT)), "archivos en", OUT)


if __name__ == "__main__":
    main()
