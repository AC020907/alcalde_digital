"""Arte de la Ruta de la Verdad (plataformero), generado de forma reproducible.

    python tools/arte/plataformas_arte.py

Escribe game/gui/plataformas/v2/*.png. Estilo de Civitas: formas planas, contorno de tinta (#2b2440),
paleta de la interfaz, sin brillos ni degradados. Todo se dibuja al doble (o cuadruple) del tamano en
pantalla y se muestra reducido, para que el contorno quede limpio.

No toca ningun personaje oficial: el protagonista del plataformero es un avatar propio del minijuego.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(RAIZ, "game", "gui", "plataformas", "v2")
FUENTE = os.path.join(RAIZ, "game", "fonts", "Roboto-Regular.ttf")

TINTA = (43, 36, 64, 255)
NOCHE = (18, 13, 28, 255)
PAPEL = (251, 246, 238, 255)
LILA = (201, 184, 216, 255)
MORADO = (58, 51, 80, 255)
MORADO2 = (74, 63, 102, 255)
MORADO3 = (96, 84, 128, 255)
VINO = (140, 47, 75, 255)
RUMOR = (209, 73, 91, 255)
TEAL = (47, 158, 143, 255)
AMBAR = (232, 176, 75, 255)
FRENO = (61, 126, 166, 255)
PIEL = (246, 214, 186, 255)
PELO = (52, 40, 66, 255)

T = 144          # tile a 2x (en pantalla 72 px)
L = 7            # grosor del contorno a 2x


def lienzo(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def guardar(img, nombre):
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, nombre + ".png"), optimize=True)


# ------------------------------------------------------------------ tiles solidos (autotiling 4 bits)
def solido(arriba, izq, der, abajo, variante):
    """Bloque de la infraestructura de NOVA. Los lados expuestos llevan contorno; los internos no (sin costuras)."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, T, T], fill=MORADO)
    # ranuras de servidor: lineas horizontales continuas de tile a tile
    for y in (52, 96):
        d.rectangle([0, y, T, y + 5], fill=MORADO2)
    # remaches/LED en patron alterno para que no se note la repeticion
    rnd = random.Random(variante)
    for x in (24, 72, 120):
        if rnd.random() < 0.45:
            d.ellipse([x - 5, 70, x + 5, 80], fill=TINTA)
    if variante % 3 == 0:
        d.rectangle([96, 112, 114, 118], fill=TEAL)
    if arriba:
        d.rectangle([0, 0, T, 30], fill=LILA)
        d.rectangle([0, 30, T, 30 + L], fill=TINTA)
        for x in range(10, T, 36):
            d.rectangle([x, 10, x + 16, 16], fill=(230, 220, 238, 255))
    if izq:
        d.rectangle([0, 0, L, T], fill=TINTA)
    if der:
        d.rectangle([T - L, 0, T, T], fill=TINTA)
    if abajo:
        d.rectangle([0, T - L, T, T], fill=TINTA)
    if arriba:
        d.rectangle([0, 0, T, L], fill=TINTA)
        if izq:
            d.polygon([(0, 0), (22, 0), (0, 22)], fill=(0, 0, 0, 0))
            d.line([(0, 22), (22, 0)], fill=TINTA, width=L)
        if der:
            d.polygon([(T, 0), (T - 22, 0), (T, 22)], fill=(0, 0, 0, 0))
            d.line([(T - 22, 0), (T, 22)], fill=TINTA, width=L)
    return im


# ------------------------------------------------------------------ peligros, bloques, objetos
def barrera(frame):
    """Barrera de interferencia: base con franjas de aviso (forma, no solo color) y estatica en dientes."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    base_y = T - 34
    d.rectangle([4, base_y, T - 4, T - 2], fill=TINTA)
    for i, x in enumerate(range(-20, T, 28)):
        d.polygon([(x, T - 6), (x + 14, base_y + 4), (x + 28, base_y + 4), (x + 14, T - 6)], fill=AMBAR)
    rnd = random.Random(frame * 31 + 7)
    puntos = [(6, base_y)]
    n = 6
    for i in range(n):
        x0 = 6 + (T - 12) * i / n
        alto = 46 + rnd.randint(-10, 14)
        puntos += [(x0 + (T - 12) / n / 2, base_y - alto), (x0 + (T - 12) / n, base_y)]
    d.polygon(puntos, fill=RUMOR, outline=TINTA)
    d.line(puntos + [puntos[0]], fill=TINTA, width=5, joint="curve")
    # chispas de estatica
    for _ in range(3):
        x, y = rnd.randint(16, T - 16), rnd.randint(base_y - 60, base_y - 30)
        d.line([(x - 6, y), (x + 6, y)], fill=PAPEL, width=4)
    return im


def inestable(estado):
    """Plataforma de datos que se apaga. on: solida con barra de carga; aviso: grietas y barra roja; off: fantasma."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    if estado == "off":
        for x in range(8, T - 8, 22):
            d.line([(x, 10), (x + 11, 10)], fill=LILA + (0,) if False else (201, 184, 216, 150), width=5)
            d.line([(x, T - 52), (x + 11, T - 52)], fill=(201, 184, 216, 150), width=5)
        d.line([(10, 10), (10, T - 52)], fill=(201, 184, 216, 110), width=4)
        d.line([(T - 10, 10), (T - 10, T - 52)], fill=(201, 184, 216, 110), width=4)
        return im
    d.rounded_rectangle([4, 4, T - 4, T - 48], radius=10, fill=MORADO3, outline=TINTA, width=L)
    d.rectangle([12, 12, T - 12, 30], fill=LILA)
    barra = RUMOR if estado == "aviso" else TEAL
    d.rectangle([20, 56, T - 20, 72], fill=TINTA)
    d.rectangle([24, 60, (T - 24) if estado == "on" else 60, 68], fill=barra)
    if estado == "aviso":
        d.line([(40, 6), (52, 30), (44, 44), (58, 64)], fill=TINTA, width=5)
        d.line([(100, 8), (92, 28), (104, 46)], fill=TINTA, width=5)
    # soportes
    d.rectangle([28, T - 48, 40, T - 30], fill=TINTA)
    d.rectangle([T - 40, T - 48, T - 28, T - 30], fill=TINTA)
    return im


def documento(sello=True):
    """Fragmento de evidencia: hoja con esquina doblada, lineas de texto y un sello."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 30, 18, 112, 124
    d.polygon([(x0, y0), (x1 - 24, y0), (x1, y0 + 24), (x1, y1), (x0, y1)], fill=PAPEL, outline=TINTA)
    d.line([(x0, y0), (x1 - 24, y0), (x1, y0 + 24), (x1, y1), (x0, y1), (x0, y0)], fill=TINTA, width=6, joint="curve")
    d.polygon([(x1 - 24, y0), (x1 - 24, y0 + 24), (x1, y0 + 24)], fill=LILA, outline=TINTA)
    d.line([(x1 - 24, y0), (x1 - 24, y0 + 24), (x1, y0 + 24)], fill=TINTA, width=5)
    for i, y in enumerate((48, 62, 76, 90)):
        d.line([(x0 + 12, y), (x1 - (30 if i == 3 else 14), y)], fill=MORADO3, width=5)
    if sello:
        d.ellipse([x1 - 40, y1 - 40, x1 - 6, y1 - 6], outline=RUMOR, width=5)
        d.line([(x1 - 32, y1 - 23), (x1 - 25, y1 - 16), (x1 - 14, y1 - 30)], fill=RUMOR, width=5)
    # clip
    d.rounded_rectangle([x0 + 18, y0 - 10, x0 + 30, y0 + 18], radius=6, outline=TINTA, width=5)
    return im


def antena(activa):
    """Punto de control: antena de la red ciudadana (apagada: gris; activa: bandera y ondas)."""
    im = lienzo(T, T)
    d = ImageDraw.Draw(im)
    d.rectangle([60, 40, 82, T - 4], fill=MORADO2, outline=TINTA, width=5)
    d.rectangle([44, T - 20, 98, T - 2], fill=TINTA)
    cabeza = TEAL if activa else MORADO3
    d.ellipse([50, 18, 92, 54], fill=cabeza, outline=TINTA, width=6)
    if activa:
        d.polygon([(82, 56), (128, 70), (82, 86)], fill=TEAL, outline=TINTA)
        d.line([(82, 56), (128, 70), (82, 86)], fill=TINTA, width=5)
        for r in (34, 50):
            d.arc([71 - r, 36 - r, 71 + r, 36 + r], 200, 340, fill=TEAL, width=5)
    return im


def archivo():
    """Meta: la puerta del archivo original (2 tiles de alto), con letrero."""
    w, h = 216, 288
    im = lienzo(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([20, 40, w - 20, h - 4], fill=MORADO2, outline=TINTA, width=L)
    d.rectangle([48, 96, w - 48, h - 4], fill=NOCHE, outline=TINTA, width=L)
    d.rectangle([62, 110, w - 62, h - 18], fill=(36, 30, 54, 255))
    for y in range(126, h - 30, 26):
        d.rectangle([76, y, w - 76, y + 12], fill=PAPEL)
        d.rectangle([100, y + 3, w - 100, y + 9], fill=MORADO3)
    d.rounded_rectangle([12, 8, w - 12, 64], radius=10, fill=PAPEL, outline=TINTA, width=L)
    f = ImageFont.truetype(FUENTE, 30)
    texto = "ARCHIVO"
    tw = d.textlength(texto, font=f)
    d.text(((w - tw) / 2, 18), texto, font=f, fill=VINO)
    return im


# ------------------------------------------------------------------ protagonista (avatar del minijuego)
def avatar(pose, fase=0.0):
    """Lienzo 224 x 256 (4x de 56 x 64). Pies abajo al centro, como el sprite anterior (misma caja de juego)."""
    W, H = 224, 256
    im = lienzo(W, H)
    d = ImageDraw.Draw(im)
    cx = W // 2
    suelo = H - 6
    bob = 0
    # angulos de piernas y brazos (grados desde la vertical; + hacia delante = derecha)
    if pose == "idle":
        pi, pd, bi, bd, bob = 4, -4, 8, -8, int(2 * math.sin(fase * math.pi))
    elif pose == "corre":
        a = math.sin(fase * 2 * math.pi)
        pi, pd = 38 * a, -38 * a
        bi, bd = -42 * a, 42 * a
        bob = -int(6 * abs(math.cos(fase * 2 * math.pi)))
    elif pose == "salto":
        pi, pd, bi, bd, bob = 30, -55, -150, -120, -6
    elif pose == "cae":
        pi, pd, bi, bd, bob = 18, -18, -125, 125, -2
    elif pose == "recoge":
        pi, pd, bi, bd, bob = 8, -8, -170, 170, -4
    elif pose == "dano":
        pi, pd, bi, bd, bob = 40, -10, -60, 100, 0
    elif pose == "victoria":
        pi, pd, bi, bd, bob = 10, -10, -160, 30, -8
    else:
        pi, pd, bi, bd = 0, 0, 0, 0
    cadera_y = suelo - 62 + bob
    hombro_y = cadera_y - 58

    def miembro(x, y, ang, largo, grosor, color, pie=False):
        r = math.radians(ang)
        x2, y2 = x + largo * math.sin(r), y + largo * math.cos(r)
        d.line([(x, y), (x2, y2)], fill=TINTA, width=grosor + 10)
        d.line([(x, y), (x2, y2)], fill=color, width=grosor)
        if pie:
            d.ellipse([x2 - 15, y2 - 9, x2 + 17, y2 + 9], fill=TINTA)
        else:
            d.ellipse([x2 - 10, y2 - 10, x2 + 10, y2 + 10], fill=PIEL, outline=TINTA, width=5)

    # pierna y brazo de atras (mas oscuros)
    miembro(cx - 8, cadera_y, pd, 52, 16, PELO, pie=True)
    miembro(cx - 10, hombro_y + 8, bd, 44, 13, (70, 60, 110, 255))
    # bufanda (la cola ondea detras)
    ondea = math.sin(fase * 2 * math.pi) * 8
    cola = [(cx - 14, hombro_y - 2), (cx - 52, hombro_y + 4 + ondea), (cx - 74, hombro_y - 6 - ondea),
            (cx - 66, hombro_y + 14 + ondea), (cx - 20, hombro_y + 14)]
    d.polygon(cola, fill=RUMOR, outline=TINTA)
    d.line(cola + [cola[0]], fill=TINTA, width=5, joint="curve")
    # torso: chaqueta del alcalde
    d.rounded_rectangle([cx - 28, hombro_y - 4, cx + 28, cadera_y + 8], radius=18, fill=(91, 79, 154, 255),
                        outline=TINTA, width=6)
    d.line([(cx, hombro_y + 6), (cx, cadera_y + 4)], fill=TINTA, width=4)
    d.rectangle([cx - 24, hombro_y - 8, cx + 24, hombro_y + 8], fill=RUMOR, outline=TINTA, width=5)
    # pierna y brazo de delante
    miembro(cx + 8, cadera_y, pi, 52, 16, (60, 50, 84, 255), pie=True)
    miembro(cx + 10, hombro_y + 8, bi, 44, 13, (110, 98, 176, 255))
    # cabeza
    hy = hombro_y - 44
    d.ellipse([cx - 40, hy - 40, cx + 40, hy + 40], fill=PIEL, outline=TINTA, width=6)
    d.chord([cx - 42, hy - 44, cx + 42, hy + 30], 180, 360, fill=PELO, outline=TINTA, width=6)
    d.polygon([(cx + 6, hy - 14), (cx + 40, hy - 10), (cx + 36, hy - 30)], fill=PELO)
    if pose == "dano":
        for ox in (6, 26):
            d.line([(cx + ox - 6, hy - 2), (cx + ox + 6, hy + 10)], fill=TINTA, width=5)
            d.line([(cx + ox + 6, hy - 2), (cx + ox - 6, hy + 10)], fill=TINTA, width=5)
    else:
        for ox in (8, 28):
            d.ellipse([cx + ox - 6, hy - 2, cx + ox + 6, hy + 12], fill=TINTA)
    if pose in ("victoria", "recoge"):
        d.arc([cx + 6, hy + 10, cx + 30, hy + 26], 10, 170, fill=TINTA, width=5)
    d.ellipse([cx + 30, hy + 12, cx + 40, hy + 20], fill=(240, 160, 160, 255))
    if pose == "recoge":
        hoja = documento(sello=False).resize((64, 64), Image.LANCZOS)
        im.alpha_composite(hoja, (cx - 32, hombro_y - 120))
    return im


# ------------------------------------------------------------------ fondos con parallax (1920 x 1080, enlazables)
def fondo_lejos():
    """Ciudad Nova (el panorama oficial del juego) entintada: el sistema de NOVA es un espejo de la ciudad."""
    pan = Image.open(os.path.join(RAIZ, "game", "images", "bg", "panorama.jpg")).convert("L")
    pan = ImageOps.autocontrast(pan, cutoff=2)
    color = ImageOps.colorize(pan, black=(22, 16, 36), white=(112, 96, 150))
    color = color.filter(ImageFilter.GaussianBlur(1.2))
    im = color.convert("RGBA")
    velo = Image.new("RGBA", im.size, (18, 13, 28, 120))
    im.alpha_composite(velo)
    # se refleja para enlazar sin costura al repetir
    doble = Image.new("RGBA", (3840, 1080))
    doble.paste(im, (0, 0))
    doble.paste(ImageOps.mirror(im), (1920, 0))
    return doble


def fondo_medio():
    """Torres de NOVA: servidores y pantallas con publicaciones en bucle. Planas, con contorno."""
    W, H = 3840, 1080
    im = lienzo(W, H)
    d = ImageDraw.Draw(im)
    rnd = random.Random(11)
    f = ImageFont.truetype(FUENTE, 26)
    x = 0
    textos = ("#AguaEnvenenada", "COMPARTE YA", "Los medios callan", "18.900 reposts", "NO LA TOMEN")
    while x < W:
        w = rnd.randint(150, 260)
        h = rnd.randint(360, 720)
        top = H - h
        d.rectangle([x, top, x + w, H], fill=(46, 39, 70, 255), outline=TINTA, width=6)
        d.rectangle([x, top, x + w, top + 22], fill=(64, 55, 94, 255), outline=TINTA, width=6)
        for yy in range(top + 50, H - 40, 46):
            for xx in range(x + 18, x + w - 24, 34):
                if rnd.random() < 0.55:
                    d.rectangle([xx, yy, xx + 18, yy + 8], fill=(30, 24, 48, 255))
                elif rnd.random() < 0.15:
                    d.rectangle([xx, yy, xx + 18, yy + 8], fill=(85, 150, 140, 255))
        if rnd.random() < 0.55 and w > 170:
            # pantalla con una publicacion del rumor (misma tarjeta de CivitasNet)
            sy = top + 70
            d.rectangle([x + 16, sy, x + w - 16, sy + 110], fill=(225, 216, 230, 255), outline=TINTA, width=6)
            d.rectangle([x + 16, sy, x + 26, sy + 110], fill=(170, 70, 90, 255))
            t = rnd.choice(textos)
            fs = 26
            while fs > 12 and d.textlength(t, font=ImageFont.truetype(FUENTE, fs)) > w - 64:
                fs -= 2
            d.text((x + 36, sy + 18), "@verdad.oculta", font=ImageFont.truetype(FUENTE, 18), fill=(140, 47, 75, 255))
            d.text((x + 36, sy + 52), t, font=ImageFont.truetype(FUENTE, fs), fill=TINTA)
        if rnd.random() < 0.35:
            d.line([(x + w // 2, top), (x + w // 2, top - 70)], fill=TINTA, width=6)
            d.ellipse([x + w // 2 - 12, top - 92, x + w // 2 + 12, top - 68], fill=(170, 70, 90, 255), outline=TINTA, width=5)
        x += w + rnd.randint(30, 90)
    # Capa media apagada: que no compita con la zona de juego.
    velo = Image.new("RGBA", im.size, (18, 13, 28, 255))
    velo.putalpha(im.split()[3].point(lambda v: int(v * 0.42)))
    im.alpha_composite(velo)
    return im


def primer_plano():
    """Cables colgando en el borde superior (primer plano, se mueve mas rapido). No toca la zona de juego."""
    W, H = 3840, 260
    im = lienzo(W, H)
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    x = 0
    while x < W:
        ancho = rnd.randint(380, 700)
        caida = rnd.randint(70, 170)
        pts = [(x + ancho * t / 30.0, 10 + caida * math.sin(math.pi * t / 30.0)) for t in range(31)]
        d.line(pts, fill=(14, 10, 22, 255), width=14, joint="curve")
        if rnd.random() < 0.5:
            px, py = pts[15]
            d.rectangle([px - 18, py, px + 18, py + 34], fill=(14, 10, 22, 255))
            d.rectangle([px - 8, py + 34, px + 8, py + 44], fill=(170, 70, 90, 255))
        x += ancho - rnd.randint(40, 160)
    d.rectangle([0, 0, W, 14], fill=(14, 10, 22, 255))
    return im


def main():
    for m in range(16):
        arriba, izq, der, abajo = bool(m & 1), bool(m & 2), bool(m & 4), bool(m & 8)
        for v in range(2):
            guardar(solido(arriba, izq, der, abajo, v), "solido_%d_%d" % (m, v))
    for f in range(3):
        guardar(barrera(f), "barrera_%d" % f)
    for e in ("on", "aviso", "off"):
        guardar(inestable(e), "inestable_" + e)
    guardar(documento(), "documento")
    guardar(antena(False), "antena_off")
    guardar(antena(True), "antena_on")
    guardar(archivo(), "archivo")
    for i in range(2):
        guardar(avatar("idle", i / 2.0), "av_idle_%d" % i)
    for i in range(6):
        guardar(avatar("corre", i / 6.0), "av_corre_%d" % i)
    for p in ("salto", "cae", "recoge", "dano", "victoria"):
        guardar(avatar(p, 0.25), "av_" + p)
    guardar(fondo_lejos(), "fondo_lejos")
    guardar(fondo_medio(), "fondo_medio")
    guardar(primer_plano(), "primer_plano")
    print("ok:", len(os.listdir(OUT)), "archivos en", OUT)


if __name__ == "__main__":
    main()
