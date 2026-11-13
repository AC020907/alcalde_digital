## Finales cinematograficos (remaster): solo presentacion. El texto, el orden y la logica de los finales
## (clases/Destinos.py, clases/Eleccion.py) no cambian. Cada desenlace tiene su color, su camara y una capa
## propia; el escrutinio cuenta los votos EXACTOS del motor; el juego cierra con el logo antes del menu.

init -1 python:
    import random as _fin_random

    # Identidad de cada desenlace. Color de acento = el del Archivo de Destinos (clases/Destinos.py).
    FINAL_CINE = {
        "informada": {"tono": "#ffe7c4", "brillo": 0.04, "sat": 1.0},
        "dividida": {"tono": "#e8dcd2", "brillo": -0.02, "sat": 0.55},
        "caos": {"tono": "#ffb3b3", "brillo": -0.06, "sat": 0.8},
        "mandato": {"tono": "#b8bce8", "brillo": -0.05, "sat": 0.45},
        "secreto": {"tono": "#f3ead8", "brillo": 0.02, "sat": 0.9},
    }

    def fin_matriz(final):
        e = FINAL_CINE[final]
        return TintMatrix(e["tono"]) * SaturationMatrix(e["sat"]) * BrightnessMatrix(e["brillo"])

    CAOS_TEXTOS = ("GANÓ VEGA: aquí las actas", "FRAUDE en la mesa 14", "El alcalde ganó por 3 votos",
                   "Contaron dos veces el Barrio Sur", "NO CREAN LAS CIFRAS OFICIALES", "Ya hay resultados (de verdad)",
                   "Video: queman tarjetones", "Mañana repiten la elección")

    class CapaCaos(renpy.Displayable):
        """Saturacion informativa: publicaciones contradictorias que se cruzan detras de los personajes."""
        def __init__(self, **kw):
            super(CapaCaos, self).__init__(**kw)
            rnd = _fin_random.Random(7)
            self.tarjetas = [(rnd.choice(CAOS_TEXTOS), rnd.uniform(0, 1920), rnd.uniform(60, 640),
                              rnd.choice((-1, 1)) * rnd.uniform(18, 46), rnd.uniform(-3, 3)) for _ in range(11)]

        def render(self, width, height, st, at):
            r = renpy.Render(width, height)
            mov = 0 if persistent.reducir_movimiento else st
            for texto, x, y, v, giro in self.tarjetas:
                xx = (x + v * mov) % (width + 600) - 300
                t = Fixed(Solid("#fbf6ee"), Solid("#d1495b", xsize=8),
                          Text(texto, size=24, bold=True, color="#2b2440", xpos=24, ypos=20),
                          Text("@cuenta_%d · hace 1 min" % int(abs(v)), size=16, color="#8b84a8", xpos=24, ypos=56),
                          xysize=(420, 92))
                img = renpy.render(Transform(t, rotate=giro, alpha=0.55), width, height, st, at)
                r.blit(img, (int(xx), int(y)))
            if not persistent.reducir_movimiento:
                renpy.redraw(self, max(0.04, AP_REFRESCO))
            return r

    class CapaGrieta(renpy.Displayable):
        """Ciudad Dividida: una grieta parte la imagen en dos mitades que ya no coinciden."""
        def __init__(self, **kw):
            super(CapaGrieta, self).__init__(**kw)
            rnd = _fin_random.Random(3)
            self.puntos = [(960 + rnd.randint(-40, 40), y) for y in range(-20, 1120, 70)]

        def render(self, width, height, st, at):
            r = renpy.Render(width, height)
            p = 1.0 if persistent.reducir_movimiento else min(1.0, st / 1.6)
            n = max(2, int(len(self.puntos) * p))
            pts = self.puntos[:n]
            izq = renpy.render(Transform(Solid("#2f9e8f"), alpha=0.10), width // 2, height, st, at)
            der = renpy.render(Transform(Solid("#8c2f4b"), alpha=0.12), width // 2, height, st, at)
            r.blit(izq, (0, 0))
            r.blit(der, (width // 2, 0))
            c = r.canvas()
            c.lines("#120d1c", False, pts, 14)
            c.lines("#fbf6ee", False, [(x + 5, y) for x, y in pts], 3)
            if p < 1.0:
                renpy.redraw(self, AP_REFRESCO)
            return r

    class CapaExpediente(renpy.Displayable):
        """Fuente Abierta: las piezas del expediente aparecen y se unen con hilo, como en una pared de redaccion."""
        PIEZAS = (("RSN-Scheduler", "panel de programación", 140, 120), ("Resonancia Consultores", "factura a las dos campañas", 1420, 150),
                  ("Informe del Acueducto", "era una tubería", 160, 520), ("@verdad.oculta", "creada el domingo", 1450, 560))

        def render(self, width, height, st, at):
            r = renpy.Render(width, height)
            c = None
            prev = None
            for i, (titulo, sub, x, y) in enumerate(self.PIEZAS):
                t0 = 0.4 + i * 0.5
                p = 1.0 if persistent.reducir_movimiento else max(0.0, min(1.0, (st - t0) / 0.4))
                if p <= 0:
                    break
                ficha = Fixed(Solid("#2b2440"), Fixed(Solid("#fbf6ee"), xysize=(332, 104), pos=(6, 6)),
                              Text(titulo, size=24, bold=True, color="#8c2f4b", xpos=24, ypos=22),
                              Text(sub, size=19, color="#2b2440", xpos=24, ypos=60), xysize=(344, 116))
                r.blit(renpy.render(Transform(ficha, alpha=p, rotate=(-1.5 if i % 2 else 1.2)), width, height, st, at),
                       (x, y + int((1 - p) * 20)))
                centro = (x + 172, y + 58)
                if prev is not None:
                    if c is None:
                        c = r.canvas()
                    q = min(1.0, p * 1.4)
                    fin = (int(prev[0] + (centro[0] - prev[0]) * q), int(prev[1] + (centro[1] - prev[1]) * q))
                    c.line("#d1495b", prev, fin, 4)
                prev = centro
            if not persistent.reducir_movimiento and st < 3.5:
                renpy.redraw(self, AP_REFRESCO)
            return r

    def fin_votos(votos, retraso, dur):
        def f(st, at):
            k = 1.0 if persistent.reducir_movimiento else max(0.0, min(1.0, (st - retraso) / dur))
            k = k * k * (3 - 2 * k)
            return Text("{:,}".format(int(votos * k)).replace(",", ".") + " votos", size=26, bold=True, color="#2b2440"), (None if k >= 1 else 0.03)
        return DynamicDisplayable(f)

    def fin_mesas(dur):
        def f(st, at):
            k = 1.0 if persistent.reducir_movimiento else max(0.0, min(1.0, st / dur))
            return Text("MESAS ESCRUTADAS  %d%%" % int(100 * k), size=18, bold=True, color="#8c2f4b", kerning=3), (None if k >= 1 else 0.05)
        return DynamicDisplayable(f)


## ---------------- Camara y color de cada desenlace (se suman a la escena; no cambian lo que pasa) ----------------
transform fin_informada:
    # Esperanza: la luz sube y la camara se abre hacia el cielo.
    matrixcolor fin_matriz("informada")
    zoom 1.08 yalign 0.7 xalign 0.5
    easeout (0.1 if persistent.reducir_movimiento else 9.0) zoom 1.0 yalign 0.35

transform fin_dividida:
    matrixcolor fin_matriz("dividida")
    zoom 1.04 xalign 0.5 yalign 0.5

transform fin_caos:
    # Camara en mano: pequenos desvios sin ritmo regular.
    matrixcolor fin_matriz("caos")
    zoom 1.06 xalign 0.5 yalign 0.5
    block:
        ease (0.1 if persistent.reducir_movimiento else 1.3) xalign 0.47 yalign 0.52
        ease (0.1 if persistent.reducir_movimiento else 1.1) xalign 0.53 yalign 0.49
        ease (0.1 if persistent.reducir_movimiento else 1.5) xalign 0.5 yalign 0.51
        repeat

transform fin_mandato:
    # Ambiguedad: frio, y la camara se cierra despacio sobre el poder.
    matrixcolor fin_matriz("mandato")
    zoom 1.0 xalign 0.5 yalign 0.4
    linear (0.1 if persistent.reducir_movimiento else 14.0) zoom 1.12

transform fin_secreto:
    matrixcolor fin_matriz("secreto")
    zoom 1.1 xalign 0.5 yalign 0.6
    easeout (0.1 if persistent.reducir_movimiento else 10.0) zoom 1.0 yalign 0.4

transform fin_franjas:
    # Bandas de cine que entran (Mandato): el encuadre se estrecha.
    alpha 0.0
    linear 1.2 alpha 1.0

image fin_capa_caos = CapaCaos()
image fin_capa_grieta = CapaGrieta()
image fin_capa_expediente = CapaExpediente()
image fin_capa_franjas = Fixed(Solid("#0b0812", xysize=(1920, 96)), Solid("#0b0812", xysize=(1920, 96), ypos=984), xysize=(1920, 1080))

transform fin_entra(retraso):
    alpha 0.0 yoffset (0 if persistent.reducir_movimiento else 18)
    pause retraso
    easein 0.45 alpha 1.0 yoffset 0

## ---------------- Cartela de cada desenlace ----------------
screen final_cartela(final):
    modal True
    $ d = destinos.DESTINOS[final]
    add Solid("#120d1c")
    vbox:
        align (0.5, 0.46)
        spacing 18
        text "DESENLACE" font AP_FUENTE_FINA size 26 kerning 14 color "#c9b8d8" xalign 0.5 at fin_entra(0.1)
        text d["titulo"].upper() font AP_FUENTE_FINA size 96 kerning 8 color "#fbf6ee" xalign 0.5 at fin_entra(0.35)
        fixed:
            xysize (620, 24)
            xalign 0.5
            at fin_entra(0.7)
            add Solid("#c9b8d8", xysize=(620, 3), ypos=10)
            add circulo(d["color"], "#2b2440", 11) xpos 299 ypos 1
        text d["misterio"] size 26 color "#c9b8d8" xalign 0.5 at fin_entra(1.0)
    timer 3.6 action Return()
    key "dismiss" action Return()
    key "civ_accion" action Return()

## ---------------- Escrutinio ----------------
## Los votos son los de clases/Eleccion.escrutinio_historia: se cuentan hasta la cifra exacta.
screen escrutinio_historia(e):
    modal True
    zorder 60
    default revelado = persistent.reducir_movimiento
    $ maximo = max(1, max(c["votos"] for c in e["candidatos"]))
    $ dur = 2.6
    add Solid("#120d1c")
    add Transform("images/bg/mapa.jpg", zoom=0.625, alpha=0.22)
    add Solid("#120d1c", alpha=0.35)
    fixed at fin_entra(0.0):
        align (0.5, 0.5)
        xysize (1400, 900)
        add Solid("#2b2440")
        frame:
            pos (10, 10)
            xysize (1380, 880)
            background Solid("#fbf6ee")
            padding (60, 44)
            vbox:
                spacing 16
                hbox:
                    xfill True
                    text "ELECCIONES DE CIUDAD NOVA" font AP_FUENTE_FINA size 34 kerning 6 color "#2b2440"
                    add fin_mesas(dur) xalign 1.0 yalign 0.5
                if revelado:
                    if e["impugnado"]:
                        text "Resultado impugnado: cada bando tiene sus propias cifras." size 34 bold True color "#d1495b" at fin_entra(0.0)
                    else:
                        text "Gana %s" % e["ganador_nombre"] size 44 bold True color "#2b2440" at fin_entra(0.0)
                else:
                    text "Contando votos…" size 44 bold True color "#8b84a8"
                null height 4
                for i, c in enumerate(e["candidatos"]):
                    $ gana = revelado and c["id"] == e["ganador"] and not e["impugnado"]
                    hbox:
                        spacing 18
                        at fin_entra(0.15 + i * 0.1)
                        fixed:
                            xysize (64, 64)
                            yalign 0.5
                            if c["id"] == "vega":
                                add circulo("#efe8f5", "#2b2440", 31)
                                add Transform(retrato_lado("tomas", "seria"), zoom=0.27) align (0.5, 0.5)
                            else:
                                add circulo("#8c2f4b" if gana else "#e6deee", "#2b2440", 31)
                                text ("TÚ" if c["id"] == "alcalde" else "".join(p[0] for p in c["nombre"].split()[:2])) size 22 bold True color ("#fbf6ee" if gana else "#2b2440") align (0.5, 0.5)
                        text c["nombre"] size 26 bold gana color "#2b2440" min_width 280 yalign 0.5
                        bar value AnimatedValue(c["votos"], maximo, (0.01 if persistent.reducir_movimiento else dur), 0) xsize 520 ysize 26 yalign 0.5 left_bar Solid("#8c2f4b" if gana else "#a7a5f2") right_bar Solid("#ece6f5")
                        add fin_votos(c["votos"], 0.0, dur) yalign 0.5
                if revelado:
                    text "Abstención: %s personas" % "{:,}".format(e["abstencion"]).replace(",", ".") size 20 italic True color "#5b4f72" at fin_entra(0.1)
                    text "¿Por qué este resultado?" size 26 bold True color "#2b2440" at fin_entra(0.2)
                    for k, linea in enumerate(e["explicacion"]):
                        text "· " + linea size 21 color "#2b2440" at fin_entra(0.3 + k * 0.15)
                    textbutton "Continuar" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return() default_focus True at fin_entra(0.4 + len(e["explicacion"]) * 0.15)
    if not revelado:
        timer (dur + 0.5) action [SetScreenVariable("revelado", True), Function(sfx, "logro")]
        key "dismiss" action SetScreenVariable("revelado", True)
        key "civ_accion" action SetScreenVariable("revelado", True)
    else:
        key "civ_accion" action Return()

## ---------------- Cierre ----------------
screen cierre_civitas(final):
    modal True
    $ d = destinos.DESTINOS[final]
    add Solid("#120d1c")
    add TituloRed()
    vbox at fin_entra(1.8):
        xalign 0.5 ypos 660
        spacing 14
        text "Tu destino: %s" % d["titulo"] size 30 bold True color d["color"] xalign 0.5
        text ("Destinos descubiertos: %d de %d" % (len(finales_descubiertos()), len(destinos.FINALES))) size 22 color "#c9b8d8" xalign 0.5
        null height 20
        text "Gracias por jugar." font AP_FUENTE_FINA size 34 kerning 4 color "#fbf6ee" xalign 0.5
    timer 6.0 action Return()
    key "dismiss" action Return()
    key "civ_accion" action Return()
