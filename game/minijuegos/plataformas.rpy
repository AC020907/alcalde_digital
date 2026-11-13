## Ruta de la Verdad - Infiltracion NOVA: plataformero 2D (motor en clases/Plataformas.py).
## Es la respuesta del jugador a La Gran Viralizacion: entra al sistema de NOVA y rescata la evidencia original.
## El motor avanza a paso fijo (60 ticks/s) con un acumulador: la dificultad no depende de los FPS.
##   Teclado: A/D o flechas para moverse · Espacio, W o flecha arriba para saltar · Esc/P: pausa
##   Mando:   cruceta o palanca · A salta · Start pausa        Tactil: botones en pantalla

init python:
    import pygame
    import math
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
    # Paleta de Civitas (remaster): papel, ambar de la evidencia, rojo del rumor, teal de la red ciudadana.
    COLOR_PARTICULA = {"evidencia": "#e8b04b", "dano": "#d1495b", "aterriza": "#c9b8d8", "salto": "#c9b8d8",
                       "control": "#2f9e8f", "meta": "#fbf6ee"}
    PLAT_V2 = PLAT_DIR + "v2/"
    PLAT_TINTA = "#2b2440"
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
            # Arte v2 (tools/arte/plataformas_arte.py): tiles a 2x (zoom 0.5 -> 72 px), avatar a 4x.
            for m in range(16):
                for v in range(2):
                    self.img["solido_%d_%d" % (m, v)] = Transform(PLAT_V2 + "solido_%d_%d.png" % (m, v), zoom=0.5)
            for n in ("barrera_0", "barrera_1", "barrera_2", "inestable_on", "inestable_aviso", "inestable_off",
                      "documento", "antena_off", "antena_on"):
                self.img[n] = Transform(PLAT_V2 + n + ".png", zoom=0.5)
            self.img["archivo"] = Transform(PLAT_V2 + "archivo.png", zoom=0.5)
            for n in ("idle_0", "idle_1", "corre_0", "corre_1", "corre_2", "corre_3", "corre_4", "corre_5",
                      "salto", "cae", "recoge", "dano", "victoria"):
                self.img[n] = PLAT_V2 + "av_" + n + ".png"
            self.za = PLAT_ESCALA / 4.0 * 1.7     # ~108 px de alto en pantalla
            niv = self.p.nivel
            self.controles_x = [fx for fy in range(niv.alto) for fx in range(niv.ancho) if niv.filas[fy][fx] == PL.CONTROL]
            self.lejos = PLAT_V2 + "fondo_lejos.png"
            self.medio = PLAT_V2 + "fondo_medio.png"
            self.cables = PLAT_V2 + "primer_plano.png"
            self.aterrizo_st = -9.0       # squash al aterrizar
            self.recoge_st = -9.0         # pose de recoger evidencia
            self.dano_st = -9.0           # sacudida y estatica al ser detectado
            self.control_st = -9.0        # onda del punto de control
            self.flecha = Transform("gui/flecha_tactil.png", zoom=2.2, alpha=0.75)
            self.flecha_izq = Transform("gui/flecha_tactil.png", zoom=2.2, alpha=0.75, xzoom=-1)

        def texto(self, s, size=24, color="#fbf6ee", bold=True):
            k = (s, size, color, bold)
            if k not in self.textos:
                if len(self.textos) > 300:
                    self.textos.clear()
                self.textos[k] = Text(s, size=size, color=color, bold=bold,
                                      outlines=([] if color in ("#2b2440", "#8c2f4b", "#8b84a8", "#d1495b") else [(3, "#2b2440", 0, 0)]))
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
                if tipo == "aterriza":
                    self.aterrizo_st = st
                if tipo == "evidencia":
                    self.recoge_st = st
                    sfx("pista")
                    self.aviso = (PL.FRAGMENTOS[dato % len(PL.FRAGMENTOS)], "#facc15", st)
                elif tipo == "dano":
                    self.dano_st = st
                    sfx("error")
                    self.aviso = ("NOVA te detectó: vuelves al último punto de control", "#fb7185", st)
                elif tipo == "control":
                    self.control_st = st
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
                if isinstance(d, str):
                    d = renpy.easy.displayable(d)
                r.blit(renpy.render(d, 1920, 1080, st, at), (int(x), int(y)))

            px = p.x / float(PL.SUB) * z
            py = p.y / float(PL.SUB) * z
            ancho_mundo = n.ancho * lado
            objetivo = max(0.0, min(ancho_mundo - 1920.0, px - 760.0 + p.mira * PLAT_ANTICIPA))
            self.camara += (objetivo - self.camara) * (0.18 if not persistent.reducir_movimiento else 1.0)
            cam = self.camara
            # Sacudida breve al ser detectado (no con movimiento reducido); solo desplaza la imagen.
            sac = 0
            if st - self.dano_st < 0.28 and not persistent.reducir_movimiento:
                sac = int(9 * math.sin((st - self.dano_st) * 70) * (1 - (st - self.dano_st) / 0.28))
            cam_v = cam + sac
            y0 = PLAT_SUELO_Y - n.alto * lado

            # Tres planos: Ciudad Nova entintada (0.12), torres de NOVA (0.35) y, al final, cables (1.25).
            r.blit(renpy.render(Solid("#120d1c"), 1920, 1080, st, at), (0, 0))
            for capa, fac, yy in ((self.lejos, 0.12, 0), (self.medio, 0.35, 40)):
                off = -(cam_v * fac) % 3840
                poner(capa, off, yy)
                poner(capa, off - 3840, yy)

            activo = PL.intermitente_activo(p.tick)
            falta = PL.PARPADEO - p.tick % PL.PARPADEO

            def es(fx, fy, ch=PL.SOLIDO):
                return 0 <= fy < n.alto and 0 <= fx < n.ancho and n.filas[fy][fx] == ch

            fx0 = max(0, int(cam_v // lado))
            for fy in range(n.alto):
                fila = n.filas[fy]
                for fx in range(fx0, min(n.ancho, fx0 + 29)):
                    ch = fila[fx]
                    if ch == ".":
                        continue
                    x, y = fx * lado - cam_v, y0 + fy * lado
                    if ch == PL.SOLIDO:
                        # Autotiling: los lados expuestos llevan contorno de tinta; los internos se unen sin costura.
                        m = ((not es(fx, fy - 1)) * 1 | (not es(fx - 1, fy)) * 2 | (not es(fx + 1, fy)) * 4
                             | (fy + 1 < n.alto and not es(fx, fy + 1)) * 8)
                        poner(self.img["solido_%d_%d" % (m, (fx + fy) % 2)], x, y)
                    elif ch == PL.PINCHO:
                        poner(self.img["barrera_%d" % (int(st * 9 + fx) % 3)], x, y)
                    elif ch == PL.INTERMITENTE:
                        # Aviso medio segundo antes de cambiar: cambia la forma (grietas, barra), no solo el color.
                        estado = "aviso" if (falta < 30 and activo) else ("on" if activo else "off")
                        tiembla = 3 if estado == "aviso" and not persistent.reducir_movimiento else 0
                        poner(self.img["inestable_" + estado], x + (tiembla if int(st * 30) % 2 else -tiembla), y)
                    elif ch == PL.EVIDENCIA:
                        if n.evidencias.index((fx, fy)) not in p.recogidas:
                            flota = 0 if persistent.reducir_movimiento else math.sin(st * 3 + fx) * 6
                            gira = 0 if persistent.reducir_movimiento else math.sin(st * 2 + fx) * 6
                            poner(Transform(self.img["documento"], rotate=gira), x - 8, y + flota - 8)
                    elif ch == PL.CONTROL:
                        on = p.control == (fx, fy)
                        poner(self.img["antena_on" if on else "antena_off"], x, y)
                        if on and st - self.control_st < 0.8:
                            k = (st - self.control_st) / 0.8
                            rr = renpy.Render(1920, 1080)
                            rr.canvas().circle("#2f9e8f", (int(x + lado / 2), int(y + 18)), int(20 + 90 * k), 4)
                            r.blit(rr, (0, 0))
                    elif ch == PL.META:
                        poner(self.img["archivo"], x - 18, y - lado)

            # Jugador: pose segun el estado del motor (sin tocar su caja); squash al aterrizar.
            if p.respawn > 0:
                cuadro = "dano"
            elif p.completado():
                cuadro = "victoria"
            elif st - self.recoge_st < 0.35:
                cuadro = "recoge"
            elif not p.en_suelo:
                cuadro = "salto" if p.vy < 0 else "cae"
            elif abs(p.vx) > 12:
                cuadro = "corre_%d" % (int(st * 14) % 6)
            else:
                cuadro = "idle_%d" % (int(st * 2) % 2)
            sx, sy = 1.0, 1.0
            if st - self.aterrizo_st < 0.14 and not persistent.reducir_movimiento:
                sx, sy = 1.12, 0.86
            if not (p.respawn > 0 and int(st * 14) % 2):
                # El avatar se dibuja mayor que su caja (legible a 1080p); pies sobre el borde inferior de la caja.
                ancho_img, alto_img = 224 * self.za * sx, 256 * self.za * sy
                img = Transform(self.img[cuadro], zoom=self.za, xzoom=(-sx if p.mira < 0 else sx), yzoom=sy)
                bx = px - cam_v + PL.ANCHO / float(PL.SUB) * z / 2.0 - ancho_img / 2.0
                by = y0 + py + PL.ALTO / float(PL.SUB) * z - alto_img + 4
                poner(img, bx, by)

            # Particulas: circulos planos con contorno (polvo, papeles, chispas), en la paleta.
            if self.particulas:
                rp = renpy.Render(1920, 1080)
                c = rp.canvas()
                for q in self.particulas:
                    tam = max(2, int(q[6] * min(1.0, q[4] * 2)))
                    cx, cy = int(q[0] - cam_v), int(y0 + q[1])
                    c.circle(PLAT_TINTA, (cx, cy), tam + 2)
                    c.circle(q[5], (cx, cy), tam)
                r.blit(rp, (0, 0))
            # Primer plano: cables (se mueven mas rapido que el juego: profundidad sin tapar plataformas).
            off = -(cam_v * 1.25) % 3840
            poner(self.cables, off, 0)
            poner(self.cables, off - 3840, 0)
            # Deteccion: estatica breve en franjas (sin destellos a pantalla completa).
            if st - self.dano_st < 0.22 and not persistent.reducir_movimiento:
                for i, yy in enumerate((180, 420, 700, 900)):
                    r.blit(renpy.render(Transform(Solid("#d1495b"), xysize=(1920, 6 + i * 3), alpha=0.35), 1920, 20, st, at),
                           (int((i * 37 + st * 900) % 60) - 30, yy))
            if self.fin_st is not None and self.p.completado():
                if not self.resultado_listo():
                    k = min(1.0, (st - self.fin_st) / 0.5)
                    r.blit(renpy.render(Transform(Solid("#120d1c"), xysize=(1920, 1080), alpha=0.55 * k), 1920, 1080, st, at), (0, 0))
                    t = self.texto("ARCHIVO RECUPERADO", 72, "#fbf6ee")
                    tr = renpy.render(t, 1920, 200, st, at)
                    r.blit(tr, (960 - tr.width // 2, 440))

            # HUD: fichas de papel (mismo lenguaje que CivitasNet) y la ruta como linea de red.
            def ficha(x, w, contenido):
                r.blit(renpy.render(Solid(PLAT_TINTA), w + 8, 64, st, at), (x - 4, 18))
                r.blit(renpy.render(Solid("#fbf6ee"), w, 56, st, at), (x, 22))
                for d_, dx, dy in contenido:
                    poner(d_, x + dx, 22 + dy)
            ficha(32, 360, [(self.texto(self.titulo, 26, "#8c2f4b"), 20, 12)])
            ficha(412, 190, [(Transform(PLAT_V2 + "documento.png", zoom=0.38), 2, -3),
                             (self.texto("%d / %d" % (len(p.recogidas), len(n.evidencias)), 30, PLAT_TINTA), 76, 9)])
            restante = max(0, (n.limite_ticks - p.tick) // PL.TICKS_S)
            ficha(622, 220, [(self.texto("%d:%02d" % (restante // 60, restante % 60), 30, "#d1495b" if restante <= 10 else PLAT_TINTA), 24, 9),
                             (self.texto("tiempo", 18, "#8b84a8", False), 126, 17)])
            ficha(862, 250, [(self.texto("%d" % p.muertes, 30, PLAT_TINTA), 22, 9),
                             (self.texto("detecciones", 18, "#8b84a8", False), 66, 17)])
            # Ruta: linea con un punto por punto de control y el archivo al final.
            avance = min(1.0, (p.x / float(PL.T)) / max(1, n.meta[0]))
            rr = renpy.Render(1920, 1080)
            c = rr.canvas()
            x0r, x1r, yr = 1170, 1860, 50
            c.line("#c9b8d8", (x0r, yr), (x1r, yr), 4)
            c.line("#2f9e8f", (x0r, yr), (int(x0r + (x1r - x0r) * avance), yr), 6)
            for cfx in self.controles_x:
                cxr = int(x0r + (x1r - x0r) * min(1.0, cfx / float(max(1, n.meta[0]))))
                c.circle(PLAT_TINTA, (cxr, yr), 10)
                c.circle("#2f9e8f" if p.x / float(PL.T) >= cfx else "#fbf6ee", (cxr, yr), 6)
            c.circle(PLAT_TINTA, (x1r, yr), 13)
            c.circle("#e8b04b", (x1r, yr), 9)
            c.circle(PLAT_TINTA, (int(x0r + (x1r - x0r) * avance), yr), 12)
            c.circle("#d1495b", (int(x0r + (x1r - x0r) * avance), yr), 8)
            r.blit(rr, (0, 0))
            if self.aviso and st - self.aviso[2] < 2.6:
                t = self.texto(self.aviso[0], 28, self.aviso[1])
                tr = renpy.render(t, 1920, 60, st, at)
                r.blit(tr, (960 - tr.width // 2, 104))
            if self.cuenta > 0:
                c = self.texto(str(int(self.cuenta / 0.8) + 1), 150, "#fbf6ee")
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
            return [renpy.easy.displayable(d) for d in list(self.img.values()) + [self.lejos, self.medio, self.cables]] + [self.flecha, self.flecha_izq]

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
    add PLAT_V2 + "fondo_lejos.png"
    add PLAT_V2 + "fondo_medio.png" ypos 40
    add Solid("#120d1cc0")
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
            for imagen, titulo, texto in (("documento", "Fragmentos", "Recógelos: son lo que más puntúa."), ("barrera_0", "Interferencia", "Si la tocas, vuelves al punto de control."),
                                          ("inestable_on", "Plataformas inestables", "Se agrietan antes de apagarse: cruza mientras están firmes."), ("antena_on", "Punto de control", "Guarda tu avance.")):
                vbox:
                    xsize 250
                    spacing 4
                    add PLAT_V2 + imagen + ".png" xalign 0.5 zoom 0.75
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

transform plat_entra(retraso):
    alpha 0.0 yoffset (0 if persistent.reducir_movimiento else 24)
    pause retraso
    easein 0.35 alpha 1.0 yoffset 0

screen plataformas_resultado(p):
    zorder 100
    $ res = p.resultado()
    $ nota = res["calificacion"]
    $ exito = res["exito"]
    add Solid("#120d1cc8")
    fixed at plat_entra(0.0):
        align (0.5, 0.5)
        xysize (1180, 680)
        add Solid("#2b2440")
        frame:
            pos (10, 10)
            xysize (1160, 660)
            background Solid("#fbf6ee")
            padding (60, 44)
            vbox:
                spacing 18
                hbox:
                    spacing 34
                    fixed:
                        xysize (170, 170)
                        add circulo("#e8b04b" if exito else "#d1495b", "#2b2440", 80) align (0.5, 0.5)
                        text nota size 110 bold True color "#2b2440" align (0.5, 0.52) at nota_golpe
                    vbox:
                        yalign 0.5
                        spacing 6
                        text ("ARCHIVO RECUPERADO" if exito else "SESIÓN CERRADA") size 50 bold True color ("#2f9e8f" if exito else "#d1495b")
                        text res["mensaje"] size 23 color "#2b2440" xmaximum 860
                        hbox:
                            spacing 10
                            add circulo("#2f9e8f" if exito else "#e6deee", "#2b2440", 11) yalign 0.5
                            text ("Objetivo cumplido: llegaste al archivo original." if exito else "Objetivo pendiente: no llegaste al archivo.") size 20 color "#5b4f72"
                hbox:
                    spacing 18
                    for i, (titulo, valor, col) in enumerate((("PUNTOS", "%d" % res["puntos"], "#2b2440"), ("EVIDENCIAS", "%d / %d" % (res["evidencias"], res["evidencias_total"]), "#8c2f4b"),
                                               ("DETECCIONES", "%d" % res["muertes"], "#d1495b" if res["muertes"] else "#2b2440"), ("TIEMPO", "%d s" % res["segundos"], "#2b2440"))):
                        frame at plat_entra(0.25 + i * 0.08):
                            background Solid("#efe8f5")
                            xsize 244
                            padding (20, 14)
                            vbox:
                                text titulo size 15 bold True color "#8b84a8" kerning 3
                                text valor size 40 bold True color col
                text "EVIDENCIA RECUPERADA" size 15 bold True color "#8c2f4b" kerning 3
                hbox:
                    spacing 14
                    box_wrap True
                    xmaximum 1040
                    if p.recogidas:
                        for k, i in enumerate(sorted(p.recogidas)[:5]):
                            frame at plat_entra(0.6 + k * 0.1):
                                background Solid("#ffffff")
                                xsize 196
                                padding (12, 10)
                                hbox:
                                    spacing 8
                                    add PLAT_V2 + "documento.png" zoom 0.28 yalign 0.0
                                    text PL.FRAGMENTOS[i % len(PL.FRAGMENTOS)] size 15 color "#2b2440" xmaximum 130
                    else:
                        text "Ningún documento: habrá que desmentir sin pruebas." size 20 color "#5b4f72"
                null height 4
                textbutton "CONTINUAR" style "boton_vn" text_style "boton_vn_text" xalign 0.5 action Return() default_focus True

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
