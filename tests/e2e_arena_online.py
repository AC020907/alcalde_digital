"""
Arena Online narrativa de extremo a extremo con NAVEGADORES REALES (Chrome headless del equipo, Playwright).

2, 3 o 4 contextos aislados -cada uno es un "telefono" o un PC- juegan la campana completa contra el servidor
local: escena (historia + pista privada) -> 5 retos que juegan TODOS (Moderacion, Rastreador, Caza-Rumores,
Ruta de la Verdad, Duelo de Frecuencias) -> resultado -> decision civica -> consecuencia -> final.
Con ?autoplay=1 (solo en localhost) cada pagina juega por el MISMO camino que una persona: botones, toques
en el lienzo, mascaras de teclado del plataformero y pulsaciones del duelo con error humano distinto por jugador.

Comprueba:
  - todos ven la misma clasificacion, el mismo resultado de cada reto y la misma final;
  - la pista privada que ve cada navegador es la de su rol y no aparece en los demas;
  - el servidor acepta lo que produce cada navegador (ningun reto queda en 0 sin desconexion);
  - latencia simulada distinta por jugador (CDP) y, con 3 jugadores, una recarga a mitad de un reto.

Uso:  python tests/e2e_arena_online.py --base http://localhost:8791 --jugadores 2,3,4 --capturas <dir>
"""
import argparse
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROLES = ["ciudadano", "periodista", "influencer", "candidato"]
LATENCIAS = [0, 150, 350, 60]
HABILIDAD = [(12, 0.0), (35, 0.05), (60, 0.12), (90, 0.25)]
RETOS = ["moderador", "rastreador", "contencion", "plataformas", "ritmo"]


def log(*a):
    print(*a, flush=True)


def estado(page):
    return page.evaluate("() => S.estado && {fase:S.estado.fase, ronda:S.estado.ronda, campana:S.estado.ronda_campana,"
                         " reto:S.estado.reto ? S.estado.reto.clave : null}")


def correr(pw, base, n, capturas, recarga):
    nav = pw.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"])
    paginas, errores = [], []
    try:
        for i in range(n):
            movil = i % 2 == 1
            ctx = nav.new_context(viewport={"width": 390, "height": 844} if movil else {"width": 1366, "height": 768},
                                  has_touch=movil, is_mobile=movil)
            page = ctx.new_page()
            page.on("pageerror", lambda e, i=i: errores.append("j%d: %s" % (i + 1, e)))
            if LATENCIAS[i]:
                cdp = ctx.new_cdp_session(page)
                cdp.send("Network.enable")
                cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": LATENCIAS[i], "downloadThroughput": -1, "uploadThroughput": -1})
            q = "?autoplay=1&sigma=%d&fallo=%.2f" % HABILIDAD[i]
            page.goto(base + "/arena" + q)
            page.fill("#nombre", "Jugador%d" % (i + 1))
            page.click('[data-rol="%s"]' % ROLES[i])
            if i == 0:
                if capturas:
                    page.screenshot(path=os.path.join(capturas, "n%d_00_inicio.png" % n), full_page=True)
                page.click("#btnCrear")
                page.wait_for_selector(".codigo-grande")
                codigo = page.inner_text(".codigo-grande").strip()
            else:
                page.fill("#codigo", codigo)
                page.click("#btnUnir")
                page.wait_for_selector("#listo")
                page.click("#listo")
            paginas.append(page)
        host = paginas[0]
        host.wait_for_selector("#empezar:not([disabled])", timeout=15000)
        if capturas:
            host.screenshot(path=os.path.join(capturas, "n%d_01_sala.png" % n), full_page=True)
        host.click("#empezar")
        log("sala %s · %d navegadores" % (codigo, n))
        vistos, fotos, recargado = [], set(), False
        privadas = {}
        t0 = time.time()
        while time.time() - t0 < 900:
            fases = [estado(p) for p in paginas]
            f0 = fases[0]
            if all(f and f["fase"] == "final" for f in fases):
                break
            if f0 and f0["fase"] == "escena":
                for k, p in enumerate(paginas):
                    pv = p.evaluate("() => S.estado.escena ? S.estado.escena.privada.texto : null")
                    if pv:
                        privadas.setdefault(f0["campana"], {})[k] = pv
            if f0 and f0["fase"] == "reto" and f0["reto"] not in vistos:
                vistos.append(f0["reto"])
                log("  reto %d: %s (%.0fs)" % (len(vistos), f0["reto"], time.time() - t0))
            clave = (f0 or {}).get("fase"), (f0 or {}).get("reto"), (f0 or {}).get("campana")
            if capturas and f0 and clave not in fotos:
                fotos.add(clave)
                time.sleep(2.5 if f0["fase"] == "reto" else 0.6)
                nombre = "n%d_%02d_%s_%s" % (n, len(fotos) + 1, f0["fase"], f0["reto"] or "")
                host.screenshot(path=os.path.join(capturas, nombre + "_pc.png"))
                if n > 1:
                    paginas[1].screenshot(path=os.path.join(capturas, nombre + "_movil.png"))
                if f0["fase"] == "reto":
                    time.sleep(5)
                    host.screenshot(path=os.path.join(capturas, nombre + "_pc_b.png"))
            if recarga and not recargado and f0 and f0["fase"] == "reto" and f0["reto"] == "contencion":
                time.sleep(4)
                p = paginas[-1]
                p.goto(base + "/arena?sala=%s&autoplay=1&sigma=35&fallo=0.05" % codigo)
                recargado = True
                log("  j%d recargo la pagina a mitad de Caza-Rumores" % n)
            time.sleep(0.5)
        else:
            raise AssertionError("la partida no termino: %s" % fases)
        assert vistos == RETOS, vistos
        # Pistas privadas: cada navegador vio la suya y ninguna se repite entre roles.
        for ronda, por_jugador in privadas.items():
            textos = list(por_jugador.values())
            assert len(set(textos)) == len(textos), (ronda, textos)
        finales = [p.evaluate("() => S.estado.final") for p in paginas]
        assert all(json.dumps(f, sort_keys=True) == json.dumps(finales[0], sort_keys=True) for f in finales), "final distinto"
        tor = finales[0]["torneo"]
        assert len(tor["clasificacion"]) == n and len(tor["pruebas"]) == 5
        for fila in tor["clasificacion"]:
            assert set(fila["pruebas"]) == set(RETOS)
        if capturas:
            host.screenshot(path=os.path.join(capturas, "n%d_99_final_pc.png" % n), full_page=True)
            if n > 1:
                paginas[1].screenshot(path=os.path.join(capturas, "n%d_99_final_movil.png" % n), full_page=True)
        assert not errores, errores
        resumen = {f["nombre"]: f["pruebas"] for f in tor["clasificacion"]}
        log("  final sincronizado en %.0fs · campeon %s · alcalde %s · ciudad %s" % (
            time.time() - t0, tor["campeon_nombre"], finales[0]["ganador_nombre"], finales[0]["ciudad"]["titulo"]))
        for nombre, pr in resumen.items():
            log("   ", nombre, pr)
        return {"jugadores": n, "segundos": round(time.time() - t0), "puntos": resumen, "campeon": tor["campeon_nombre"],
                "alcalde": finales[0]["ganador_nombre"], "ciudad": finales[0]["ciudad"]["titulo"]}
    finally:
        nav.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8791")
    ap.add_argument("--jugadores", default="2,3,4")
    ap.add_argument("--capturas", default="")
    args = ap.parse_args()
    if args.capturas:
        os.makedirs(args.capturas, exist_ok=True)
    out = []
    with sync_playwright() as pw:
        for n in [int(x) for x in args.jugadores.split(",")]:
            out.append(correr(pw, args.base, n, args.capturas, recarga=(n == 3)))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
