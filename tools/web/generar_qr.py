"""
Genera el codigo QR del juego web SOLO si la URL publicada responde por HTTPS.

Escribe:
  game/gui/qr_web.png                 -> pantalla final del Modo Feria ("sigue jugando en tu telefono")
  leaderboard/app/static/qr.png       -> pagina publica de la clasificacion (pantalla del stand)

Uso:  python tools/web/generar_qr.py https://usuario.github.io/repo/
"""
import os
import sys
import urllib.request

import qrcode

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DESTINOS = [os.path.join(RAIZ, "game", "gui", "qr_web.png"),
            os.path.join(RAIZ, "leaderboard", "app", "static", "qr.png")]


def verificar(url):
    if not url.startswith("https://"):
        sys.exit("La URL debe ser HTTPS: los navegadores moviles bloquean audio y pantalla completa sin ella.")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=15) as r:
            cuerpo = r.read(200000).decode("utf-8", "replace")
            if r.status != 200 or "renpy" not in cuerpo.lower():
                sys.exit("La URL responde (%d) pero no parece la build web de Ren'Py." % r.status)
    except Exception as e:
        sys.exit("La URL no responde todavia: %s" % e)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    verificar(url)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="#2b2440", back_color="#fbf6ee")
    for destino in DESTINOS:
        imagen.save(destino)
        print("QR ->", destino)
    print("Listo. Vuelve a exportar la build (web y PC) para que el juego muestre el QR.")


if __name__ == "__main__":
    main()
