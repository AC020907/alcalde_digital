"""
Ajustes a la build web de Ren'Py despues de exportarla:
  - aviso "gira el telefono" en pantallas verticales tactiles (el juego es 16:9);
  - titulo y descripcion de la pagina;
  - archivo .nojekyll para GitHub Pages (sirve tal cual los archivos que empiezan por "_").

Uso:  python tools/web/postbuild.py RUTA_BUILD_WEB
"""
import os
import sys

MARCA = "<!-- civitas-postbuild -->"

AVISO = MARCA + """
<style>
  #civitas-girar { display: none; position: fixed; inset: 0; z-index: 99999; background: #1b1426;
    color: #fbf6ee; font-family: system-ui, sans-serif; text-align: center; padding: 24px;
    flex-direction: column; align-items: center; justify-content: center; gap: 18px; }
  #civitas-girar .icono { width: 72px; height: 116px; border: 6px solid #a7a5f2; border-radius: 14px;
    animation: civitas-giro 2.2s ease-in-out infinite; }
  #civitas-girar p { font-size: 20px; line-height: 1.4; max-width: 320px; margin: 0; }
  #civitas-girar small { color: #a7a5f2; font-size: 15px; }
  @keyframes civitas-giro { 0%, 30% { transform: rotate(0); } 60%, 100% { transform: rotate(-90deg); } }
  @media (orientation: portrait) and (pointer: coarse) { #civitas-girar { display: flex; } }
  @media (prefers-reduced-motion: reduce) { #civitas-girar .icono { animation: none; } }
</style>
<div id="civitas-girar" role="alert">
  <div class="icono" aria-hidden="true"></div>
  <p>Gira el teléfono para jugar <b>Alcalde Digital</b> en horizontal.</p>
  <small>Consejo: activa la pantalla completa desde el menú del navegador.</small>
</div>
"""


def main(ruta):
    index = os.path.join(ruta, "index.html")
    with open(index, encoding="utf-8") as f:
        html = f.read()
    if MARCA not in html:
        html = html.replace("<body>", "<body>\n" + AVISO, 1) if "<body>" in html else html.replace("</body>", AVISO + "\n</body>", 1)
        html = html.replace("<title>Alcalde Digital</title>",
                            "<title>Alcalde Digital - Civitas</title>\n<meta name=\"description\" "
                            "content=\"Novela visual sobre desinformación: eres el alcalde de Ciudad Nova la semana antes de las elecciones.\">", 1)
        with open(index, "w", encoding="utf-8") as f:
            f.write(html)
    open(os.path.join(ruta, ".nojekyll"), "w").close()
    print("postbuild OK:", index)


if __name__ == "__main__":
    main(sys.argv[1])
