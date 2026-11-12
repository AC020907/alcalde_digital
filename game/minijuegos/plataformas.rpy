## Ruta de la Verdad - Infiltracion NOVA: plataformero 2D (motor en clases/Plataformas.py).
## Es la respuesta del jugador a La Gran Viralizacion: entra al sistema de NOVA y rescata la evidencia original.
## El motor avanza a paso fijo (60 ticks/s) con un acumulador: la dificultad no depende de los FPS.
##   Teclado: A/D o flechas para moverse · Espacio, W o flecha arriba para saltar · Esc/P: pausa
##   Mando:   cruceta o palanca · A salta · Start pausa        Tactil: botones en pantalla

init python:
    import pygame
    import math
    from clases import Plataformas as PL

    config.keymap.update({
        "civ_salto": ["K_SPACE", "K_UP", "K_w", "K_z"],
        "civ_salto_fin": ["keyup_K_SPACE", "keyup_K_UP", "keyup_K_w", "keyup_K_z"],
    })
    for _ev, _acc in (("pad_a_press", "civ_salto"), ("pad_a_release", "civ_salto_fin"),
                      ("pad_b_press", "civ_salto"), ("pad_b_release", "civ_salto_fin")):
        config.pad_bindings[_ev] = list(config.pad_bindings.get(_ev, [])) + [_acc]

    PLAT_DIR = "gui/plataformas/"
    PLAT_ESCALA = 1.5                  # 48 px del motor -> 72 px en pantalla: el nivel (11 filas) llena el alto util
    PLAT_SUELO_Y = 1010                # y en pantalla del borde inferior del nivel
    PLAT_ANTICIPA = 260                # la camara mira hacia donde corre el jugador (ve antes los obstaculos)
    COLOR_PARTICULA = {"evidencia": "#facc15", "dano": "#fb7185", "aterriza": "#c9b8d8", "salto": "#e9d5ff",
                       "control": "#5eead4", "meta": "#5eead4"}
    # Zonas tactiles (x0, y0, x1, y1): izquierda, derecha y salto.
    PLAT_ZONAS = {PL.IZQ: (30, 850, 230, 1050), PL.DER: (260, 850, 460, 1050), PL.SALTO: (1640, 820, 1890, 1050)}

    class VistaPlataformas(renpy.Displayable):
        def __init__(self, clave, extra_s=0, titulo="RUTA DE LA VERDAD", reinicio=True, **kwargs):
            super(VistaPlataformas, self).__init__(**kwargs)
            self.p = PL.Partida(clave, extra_s)
            self.clave, self.extra_s, self.reinicio = clave, extra_s, reinicio
            self.particulas = []          # [x, y, vx, vy, vida, color, tam] en px de pantalla del mundo
            self.fin_st = None            # instante en que termino la carrera (transicion antes del resultado)
            self.st = 0.0
            self.st0, self.frames = None, 0     # medicion de FPS (QA)
            self.titulo = titulo
            self.teclas = set()           # direcciones mantenidas por teclado o mando
            self.salto = False
            self.dedos = {}               # id de dedo (o "raton") -> mascara
            self.acum = 0.0
            self.ultimo = None
            self.pausa = False
            self.cuenta = 2.4             # cuenta atras antes de empezar (segundos)
            self.camara = 0.0
            self.eventos_vistos = 0
            self.aviso = None             # (texto, color, st)
            self.fin_avisado = False
            self.img = {}
            self.textos = {}
            self.tactil = renpy.variant("touch")
            # QA visual: un piloto automatico juega por el mismo motor (store.qa_plataformas_auto = habilidad 0..1).
            auto = getattr(store, "qa_plataformas_auto", None)
            self.piloto = PL.Piloto(__import__("random").Random(7), auto) if auto is not None else None
            z = PLAT_ESCALA
            for n in ("suelo", "relleno", "pincho", "bloque_on", "bloque_aviso", "bloque_off", "evidencia",
                      "control_off", "control_on"):
                self.img[n] = Transform(PLAT_DIR + n + ".png", zoom=z)
            self.img["meta"] = Transform(PLAT_DIR + "meta.png", zoom=z)
            for n in ("idle_0", "idle_1", "corre_0", "corre_1", "corre_2", "corre_3", "salto", "cae", "dano"):
                self.img[n] = Transform(PLAT_DIR + n + ".png", zoom=z)
                self.img[n + "_izq"] = Transform(PLAT_DIR + n + ".png", zoom=z, xzoom=-1)
            self.cielo = Transform(PLAT_DIR + "cielo.png", xysize=(1920, 1080))
            self.lejos = Transform(PLAT_DIR + "fondo_lejos.png", zoom=2.0)
            self.cerca = Transform(PLAT_DIR + "fondo_cerca.png", zoom=2.0)
            self.flecha = Transform("gui/flecha_tactil.png", zoom=2.2, alpha=0.75)
            self.flecha_izq = Transform("gui/flecha_tactil.png", zoom=2.2, alpha=0.75, xzoom=-1)

        def texto(self, s, size=24, color="#fbf6ee", bold=True):
            k = (s, size, color, bold)
            if k not in self.textos:
                if len(self.textos) > 300:
                    self.textos.clear()
                self.textos[k] = Text(s, size=size, color=color, bold=bold, outlines=[(3, "#0d0a1acc", 0, 0)])
            return self.textos[k]

        def mascara(self):
            m = 0
            if "civ_izq" in self.teclas:
                m |= PL.IZQ
            if "civ_der" in self.teclas:
                m |= PL.DER
            if self.salto:
                m |= PL.SALTO
            for v in self.dedos.values():
                m |= v
            return m

        def pausar(self):
            if self.p.jugando():
                self.pausa = True
                renpy.restart_interaction()

        def reanudar(self):
            self.pausa = False
            self.ultimo = None
            renpy.restart_interaction()

        def abandonar(self):
            self.pausa = False
            self.p.abandonar()
            renpy.restart_interaction()

        def reiniciar(self):
            """Reinicio rapido (Historia y Feria): la misma carrera desde el principio."""
            self.p = PL.Partida(self.clave, self.extra_s)
            self.pausa, self.cuenta, self.acum, self.ultimo = False, 1.2, 0.0, None
            self.eventos_vistos, self.fin_st, self.fin_avisado, self.camara, self.particulas = 0, None, False, 0.0, []
            renpy.restart_interaction()

        def resultado_listo(self):
            """El resultado aparece tras una breve transicion (destello al llegar al archivo)."""
            return not self.p.jugando() and self.fin_st is not None and self.st - self.fin_st > 1.1

        def chispas(self, tipo, cantidad, fuerza):
            p, z = self.p, PLAT_ESCALA
            x = p.x / float(PL.SUB) * z + PL.ANCHO / float(PL.SUB) * z / 2
            y = p.y / float(PL.SUB) * z + (PL.ALTO / float(PL.SUB) * z if tipo in ("aterriza", "salto") else PL.ALTO / float(PL.SUB) * z / 2)
            rnd = __import__("random")
            for k in range(cantidad if not persistent.reducir_movimiento else cantidad // 3):
                ang = rnd.uniform(math.pi, 2 * math.pi) if tipo in ("aterriza", "salto") else rnd.uniform(0, 2 * math.pi)
                v = rnd.uniform(0.4, 1.0) * fuerza
                self.particulas.append([x, y, math.cos(ang) * v, math.sin(ang) * v, rnd.uniform(0.35, 0.8), COLOR_PARTICULA[tipo], rnd.choice((5, 7, 9))])

        # ----- simulacion a paso fijo -----
        def simular(self, st):
            self.st = st
            if self.ultimo is None:
                self.ultimo = st
            dt = min(0.1, max(0.0, st - self.ultimo))       # tras un tiron no se "teletransporta"
            self.ultimo = st
            for q in self.particulas:
                q[0] += q[2] * dt
                q[1] += q[3] * dt
                q[3] += 900 * dt
                q[4] -= dt
            self.particulas = [q for q in self.particulas if q[4] > 0]
            if not self.p.jugando() and self.fin_st is None:
                self.fin_st = st
            if self.pausa or not self.p.jugando():
                return
            if self.cuenta > 0:
                self.cuenta -= dt
                return
            self.acum += dt
            paso = 1.0 / PL.TICKS_S
            m = self.mascara()
            while self.acum >= paso and self.p.jugando():
                self.acum -= paso
                self.p.avanzar(self.piloto.mascara(self.p) if self.piloto else m)
            for tick, tipo, dato in self.p.eventos[self.eventos_vistos:]:
                if tipo in COLOR_PARTICULA:
                    self.chispas(tipo, {"evidencia": 22, "dano": 26, "aterriza": 7, "salto": 5, "control": 16, "meta": 40}[tipo],
                                 {"evidencia": 420, "dano": 380, "aterriza": 160, "salto": 120, "control": 300, "meta": 520}[tipo])
                if tipo == "evidencia":
                    sfx("pista")
                    self.aviso = (PL.FRAGMENTOS[dato % len(PL.FRAGMENTOS)], "#facc15", st)
                elif tipo == "dano":
                    sfx("error")
                    self.aviso = ("NOVA te detectó: vuelves al último punto de control", "#fb7185", st)
                elif tipo == "control":
                    sfx("decision")
                    self.aviso = ("Punto de control", "#5eead4", st)
                elif tipo == "meta":
                    sfx("logro")
                elif tipo == "tiempo":
                    sfx("alarma")
            self.eventos_vistos = len(self.p.eventos)

        def fps(self):
            return round(self.frames / max(0.001, self.st - self.st0), 1) if self.st0 is not None else 0.0

        def render(self, width, height, st, at):
            if self.st0 is None:
                self.st0 = st
            self.frames += 1
            self.simular(st)
            p, n, z = self.p, self.p.nivel, PLAT_ESCALA
            lado = int(PL.TILE * z)
            r = renpy.Render(1920, 1080)

            def poner(d, x, y):
                r.blit(renpy.render(d, 1920, 1080, st, at), (int(x), int(y)))

            px = p.x / float(PL.SUB) * z
            py = p.y / float(PL.SUB) * z
            ancho_mundo = n.ancho * lado
            objetivo = max(0.0, min(ancho_mundo - 1920.0, px - 760.0 + p.mira * PLAT_ANTICIPA))
            self.camara += (objetivo - self.camara) * (0.18 if not persistent.reducir_movimiento else 1.0)
            cam = self.camara
            y0 = PLAT_SUELO_Y - n.alto * lado
            poner(self.cielo, 0, 0)
            poner(self.lejos, -(cam * 0.15) % 1920, 0)
            poner(self.lejos, -(cam * 0.15) % 1920 - 1920, 0)
            poner(self.cerca, -(cam * 0.35) % 1920, 0)
            poner(self.cerca, -(cam * 0.35) % 1920 - 1920, 0)

            activo = PL.intermitente_activo(p.tick)
            falta = PL.PARPADEO - p.tick % PL.PARPADEO
            fx0 = max(0, int(cam // lado))
            for fy in range(n.alto):
                fila = n.filas[fy]
                for fx in range(fx0, min(n.ancho, fx0 + 34)):
                    ch = fila[fx]
                    if ch == ".":
                        continue
                    x, y = fx * lado - cam, y0 + fy * lado
                    if ch == PL.SOLIDO:
                        poner(self.img["suelo" if fy == 0 or n.filas[fy - 1][fx] != PL.SOLIDO else "relleno"], x, y)
                    elif ch == PL.PINCHO:
                        poner(self.img["pincho"], x, y)
                    elif ch == PL.INTERMITENTE:
                        # Aviso visual medio segundo antes de cambiar (no depende del color: tambien cambia la forma).
                        poner(self.img["bloque_aviso" if falta < 30 and int(st * 10) % 2 else ("bloque_on" if activo else "bloque_off")], x, y)
                    elif ch == PL.EVIDENCIA:
                        if n.evidencias.index((fx, fy)) not in p.recogidas:
                            poner(self.img["evidencia"], x, y + math.sin(st * 3 + fx) * 5)
                    elif ch == PL.CONTROL:
                        poner(self.img["control_on" if p.control == (fx, fy) else "control_off"], x, y)
                    elif ch == PL.META:
                        poner(self.img["meta"], x - 15, y - lado)

            # jugador
            if p.respawn > 0:
                cuadro = "dano"
            elif not p.en_suelo:
                cuadro = "salto" if p.vy < 0 else "cae"
            elif abs(p.vx) > 12:
                cuadro = "corre_%d" % (int(st * 12) % 4)
            else:
                cuadro = "idle_%d" % (int(st * 2) % 2)
            if p.mira < 0:
                cuadro += "_izq"
            if not (p.respawn > 0 and int(st * 14) % 2):
                poner(self.img[cuadro], px - cam - (56 - 30) * z / 2.0, y0 + py - (64 - 42) * z)

            for q in self.particulas:
                tam = q[6]
                r.blit(renpy.render(Transform(Solid(q[5]), xysize=(tam, tam), alpha=min(1.0, q[4] * 2)), tam, tam, st, at),
                       (int(q[0] - cam - tam / 2), int(y0 + q[1] - tam / 2)))
            if self.fin_st is not None and self.p.completado():
                destello = max(0.0, 1.0 - (st - self.fin_st) / 0.9)
                if destello > 0 and not persistent.reducir_movimiento:
                    r.blit(renpy.render(Transform(Solid("#5eead4"), xysize=(1920, 1080), alpha=destello * 0.55), 1920, 1080, st, at), (0, 0))
                if not self.resultado_listo():
                    t = self.texto("ARCHIVO RECUPERADO", 90, "#5eead4")
                    tr = renpy.render(t, 1920, 200, st, at)
                    r.blit(tr, (960 - tr.width // 2, 420))

            # HUD minimo: evidencias, tiempo, muertes
            barra = renpy.render(Solid("#0d0a1acc"), 1920, 84, st, at)
            r.blit(barra, (0, 0))
            poner(self.texto(self.titulo, 30, "#f0abfc"), 40, 22)
            poner(self.img["evidencia"], 660, 12)
            poner(self.texto("%d / %d" % (len(p.recogidas), len(n.evidencias)), 34), 730, 20)
            restante = max(0, (n.limite_ticks - p.tick) // PL.TICKS_S)
            poner(self.texto("TIEMPO %d:%02d" % (restante // 60, restante % 60), 34, "#fb7185" if restante <= 10 else "#fbf6ee"), 960, 20)
            poner(self.texto("Detecciones: %d" % p.muertes, 26, "#c9b8d8"), 1330, 26)
            avance = min(1.0, (p.x / float(PL.T)) / max(1, n.meta[0]))
            r.blit(renpy.render(Solid("#3b2f6b"), 1920, 6, st, at), (0, 84))
            r.blit(renpy.render(Solid("#5eead4"), int(1920 * avance), 6, st, at), (0, 84))
            if self.aviso and st - self.aviso[2] < 2.6:
                t = self.texto(self.aviso[0], 28, self.aviso[1])
                tr = renpy.render(t, 1920, 60, st, at)
                r.blit(tr, (960 - tr.width // 2, 118))
            if self.cuenta > 0:
                c = self.texto(str(int(self.cuenta / 0.8) + 1), 150, "#facc15")
                cr = renpy.render(c, 400, 200, st, at)
                r.blit(cr, (960 - cr.width // 2, 400))
            if self.tactil:
                poner(self.flecha_izq, PLAT_ZONAS[PL.IZQ][0] + 30, PLAT_ZONAS[PL.IZQ][1] + 30)
                poner(self.flecha, PLAT_ZONAS[PL.DER][0] + 30, PLAT_ZONAS[PL.DER][1] + 30)
                poner(self.texto("SALTO", 40, "#facc15"), PLAT_ZONAS[PL.SALTO][0] + 50, PLAT_ZONAS[PL.SALTO][1] + 90)
            if self.resultado_listo() and not self.fin_avisado:
                self.fin_avisado = True
                renpy.restart_interaction()
            renpy.redraw(self, 0)
            return r

        def zona(self, x, y):
            for mascara, (x0, y0, x1, y1) in PLAT_ZONAS.items():
                if x0 - 30 <= x <= x1 + 30 and y0 - 60 <= y <= y1 + 30:
                    return mascara
            return 0

        def event(self, ev, x, y, st):
            if not self.p.jugando() or self.pausa:
                return None
            if renpy.map_event(ev, "civ_pausa") or renpy.map_event(ev, "game_menu"):
                self.pausar()
                raise renpy.IgnoreEvent()
            direccion = direccion_evento(ev)
            if direccion is not None:
                nombre, _vector, pulsada = direccion
                (self.teclas.add if pulsada else self.teclas.discard)(nombre)
                if nombre == "civ_arriba":
                    self.salto = pulsada
                raise renpy.IgnoreEvent()
            if renpy.map_event(ev, "civ_salto"):
                self.salto = True
                raise renpy.IgnoreEvent()
            if renpy.map_event(ev, "civ_salto_fin"):
                self.salto = False
                raise renpy.IgnoreEvent()
            # Tactil: varios dedos a la vez (moverse y saltar). El raton sirve de respaldo con un solo "dedo".
            tipo = ev.type
            if tipo in (getattr(pygame, "FINGERDOWN", -1), getattr(pygame, "FINGERMOTION", -1)):
                self.dedos[ev.finger_id] = self.zona(ev.x * 1920, ev.y * 1080)
                raise renpy.IgnoreEvent()
            if tipo == getattr(pygame, "FINGERUP", -1):
                self.dedos.pop(ev.finger_id, None)
                raise renpy.IgnoreEvent()
            if tipo == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.dedos["raton"] = self.zona(x, y)
                self.tactil = self.tactil or bool(self.dedos["raton"])
                raise renpy.IgnoreEvent()
            if tipo == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.dedos.pop("raton", None)
                raise renpy.IgnoreEvent()
            return None

        def visit(self):
            return list(self.img.values()) + [self.cielo, self.lejos, self.cerca, self.flecha, self.flecha_izq]

    def extra_plataformas(ajustes):
        """Traduce la ayuda narrativa del domingo (pensada para el arcade) a segundos de margen en la infiltracion."""
        if not ajustes:
            return 0
        if "extra_s" in ajustes:
            return int(ajustes["extra_s"])
        umbral = ajustes.get("umbral_viral")
        return int(round((umbral - 15000) / 150.0)) if umbral else 0


screen plataformas_tutorial(extra_s=0):
    modal True
    zorder 46
    add "bg viral"
    add Solid("#0d0a1ae0")
    frame:
        align (0.5, 0.5)
        xsize 1240
        background Frame("gui/frame.png", 30, 30)
        padding (56, 40)
        has vbox
        spacing 14
        xfill True
        text "RUTA DE LA VERDAD" size 46 bold True color "#8c2f4b" xalign 0.5
        text "INFILTRACIÓN NOVA" size 24 bold True color "#6d5bd0" xalign 0.5
        text "El rumor ya corre por toda la ciudad. La única forma de pararlo es entrar al sistema de NOVA y traer la evidencia original." size 22 color "#2b2440" xalign 0.5 text_align 0.5
        hbox:
            xalign 0.5
            spacing 40
            for imagen, titulo, texto in (("evidencia", "Fragmentos", "Recógelos: son lo que más puntúa."), ("pincho", "Interferencia", "Si la tocas, vuelves al punto de control."),
                                          ("bloque_on", "Bloques que parpadean", "Cruza mientras están encendidos."), ("control_on", "Punto de control", "Guarda tu avance.")):
                vbox:
                    xsize 250
                    spacing 4
                    add PLAT_DIR + imagen + ".png" xalign 0.5 zoom 1.4
                    text titulo size 20 bold True color "#2b2440" xalign 0.5
                    text texto size 17 color "#5b4f72" xalign 0.5 text_align 0.5
        text ("Toca las flechas para moverte y SALTO para saltar." if renpy.variant("touch") else "Muévete con A/D o las flechas. Salta con Espacio, W o flecha arriba (mantén para saltar más alto). Con mando: cruceta y A.") size 20 bold True color "#2b2440" xalign 0.5 text_align 0.5
        text "Llega al archivo del final antes de que NOVA cierre la sesión." size 20 color "#2b2440" xalign 0.5
        if extra_s > 0:
            text "Tu aliado distrae a NOVA: tienes [extra_s] segundos más." size 20 bold True color "#2f9e8f" xalign 0.5
        elif extra_s < 0:
            text "El video patrocinado alimenta a NOVA: tienes menos tiempo." size 20 bold True color "#c0392b" xalign 0.5
        textbutton "ENTRAR AL SISTEMA" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return() default_focus True

screen plataformas_ui(vista):
    modal True
    zorder 45
    add vista
    if vista.p.jugando() and not vista.pausa:
        textbutton "Pausa" style "boton_vn_compacto" text_style "boton_vn_text" xalign 0.99 ypos 96 action Function(vista.pausar)
    if vista.pausa:
        add Solid("#000000b8")
        frame:
            align (0.5, 0.5)
            background Frame("gui/frame.png", 30, 30)
            padding (56, 40)
            vbox:
                spacing 16
                text "PAUSA" size 44 bold True color "#2b2440" xalign 0.5
                textbutton "Continuar" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.reanudar) default_focus True
                if vista.reinicio:
                    textbutton "Reiniciar desde el principio" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.reiniciar)
                textbutton "Salir de la infiltración" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Function(vista.abandonar)
        key "civ_pausa" action Function(vista.reanudar)
    elif vista.resultado_listo():
        use plataformas_resultado(vista.p)

screen plataformas_resultado(p):
    zorder 100
    $ res = p.resultado()
    $ nota = res["calificacion"]
    $ color_nota = {"S": "#facc15", "A": "#22c55e", "B": "#38bdf8", "C": "#a78bfa", "D": "#ef4444"}[nota]
    add Solid("#000000b0")
    frame:
        align (0.5, 0.5)
        xsize 1040
        background "#0b1324f5"
        padding (50, 36)
        vbox:
            spacing 12
            xfill True
            text ("ARCHIVO RECUPERADO" if res["exito"] else "SESIÓN CERRADA") size 54 bold True color ("#22c55e" if res["exito"] else "#ef4444") xalign 0.5
            text nota size 150 bold True color color_nota xalign 0.5 at nota_golpe
            text res["mensaje"] size 24 color "#f1f5f9" xalign 0.5 textalign 0.5
            hbox:
                xalign 0.5
                spacing 50
                for titulo, valor, col in (("PUNTOS", "%d" % res["puntos"], "#f8fafc"), ("EVIDENCIAS", "%d / %d" % (res["evidencias"], res["evidencias_total"]), "#facc15"),
                                           ("DETECCIONES", "%d" % res["muertes"], "#f87171"), ("TIEMPO", "%d s" % res["segundos"], "#f8fafc")):
                    vbox:
                        text titulo size 16 color "#94a3b8" xalign 0.5
                        text valor size 34 bold True color col xalign 0.5
            if p.recogidas:
                text "Lo que trajiste: " + " · ".join(PL.FRAGMENTOS[i % len(PL.FRAGMENTOS)] for i in sorted(p.recogidas)[:4]) + ("…" if len(p.recogidas) > 4 else "") size 17 color "#cbd5e1" xalign 0.5 textalign 0.5
            textbutton "CONTINUAR":
                style "grafo_button"
                text_style "grafo_button_text"
                xalign 0.5
                xsize 360
                text_xalign 0.5
                default_focus True
                action Return()

## Minijuego reutilizable: Historia (nivel "historia"), Feria ("feria"), Arena ("arena") y tutorial.
label minijuego_plataformas(nivel="historia", aplicar=True, ajustes=None, tutorial=True, reinicio=True):
    $ hud_estaba_visible = renpy.get_screen("hud_ciudad") is not None
    $ ocultar_avisos_juego()
    hide screen hud_ciudad
    $ quick_menu_previo = quick_menu
    $ quick_menu = False
    window hide
    $ renpy.block_rollback()
    $ extra_plat = extra_plataformas(ajustes)
    if tutorial:
        call screen plataformas_tutorial(extra_plat)
    $ vista_plataformas = VistaPlataformas(nivel, extra_plat, reinicio=reinicio)
    call screen plataformas_ui(vista_plataformas)
    $ plataformas = vista_plataformas.p
    $ quick_menu = quick_menu_previo
    if hud_estaba_visible:
        show screen hud_ciudad
    $ renpy.block_rollback()
    $ resultado_minijuego = registrar_minijuego(plataformas.resultado(), aplicar)
    return resultado_minijuego
