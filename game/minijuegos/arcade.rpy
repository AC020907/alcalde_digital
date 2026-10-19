## Vista arcade en tiempo real (60 fps) para Caza-Rumores y el Rastreador.
## La simulacion vive en clases/CazaRumores.py y clases/Rastreador.py;
## aqui solo se dibuja y se traduce el mouse/teclado a acciones.

init python:
    import math
    import pygame
    from clases.CazaRumores import CazaRumores, focos_viralizacion
    from clases.Rastreador import RastreoEnVivo

    SONIDO_INTERCEPCION = "assets/audio/sfx/intercepcion.wav"

    COLOR_ARCADE = {
        "sano":       "#475569",
        "infectado":  "#ef4444",
        "cuarentena": "#38bdf8",
        "protegido":  "#22c55e",
        "rastro":     "#facc15",
    }

    def mezclar(c1, c2, t):
        a, b = rgba(c1), rgba(c2)
        return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def color_edad(edad):
        """Rastreador: contagio reciente = naranja, antiguo = morado (cuantizado para cachear)."""
        paso = min(7, int(edad / 2.5))
        return mezclar("#f97316", "#7e22ce", paso / 7.0)

    def posiciones_mapa(grafo, excluir):
        """Cada barrio es una zona del mapa; sus cuentas se reparten en circulo dentro de ella."""
        barrios = []
        for nodo in grafo.lista_nodos():
            barrio = grafo.perfil(nodo).get("barrio")
            if nodo not in excluir and barrio not in barrios:
                barrios.append(barrio)
        centros, posiciones = {}, {}
        for i, barrio in enumerate(barrios):
            angulo = -math.pi / 2 + 2 * math.pi * i / len(barrios)
            centros[barrio] = (960 + 650 * math.cos(angulo), 650 + 250 * math.sin(angulo))
        for barrio in barrios:
            miembros = [n for n in grafo.lista_nodos()
                        if n not in excluir and grafo.perfil(n).get("barrio") == barrio]
            cx, cy = centros[barrio]
            for j, nodo in enumerate(miembros):
                angulo = -math.pi / 2 + 2 * math.pi * j / len(miembros) + 0.4
                posiciones[nodo] = (int(cx + 115 * math.cos(angulo)), int(cy + 115 * math.sin(angulo)))
        return posiciones, centros

    def radio_arcade(grafo, nodo):
        return int(30 + min(grafo.alcance(nodo), 60) * 0.22)

    class Aro(renpy.Displayable):
        cache = {}

        def __init__(self, color, radio, grosor, **kwargs):
            super(Aro, self).__init__(**kwargs)
            self.color = color
            self.radio = radio
            self.grosor = grosor

        def render(self, width, height, st, at):
            lado = (self.radio + self.grosor) * 2
            r = renpy.Render(lado, lado)
            r.canvas().circle(rgba(self.color), (lado // 2, lado // 2), self.radio, self.grosor)
            return r

    def aro(color, radio, grosor=4):
        radio = max(6, int(radio) // 4 * 4)
        clave = (color, radio, grosor)
        if clave not in Aro.cache:
            if len(Aro.cache) > 400:
                Aro.cache.clear()
            Aro.cache[clave] = Aro(color, radio, grosor)
        return Aro.cache[clave]

    class CapaMapa(renpy.Displayable):
        """Fondo estatico: zonas de barrio y conexiones muy tenues."""

        def __init__(self, grafo, posiciones, centros, **kwargs):
            super(CapaMapa, self).__init__(**kwargs)
            self.grafo = grafo
            self.posiciones = posiciones
            self.centros = centros

        def render(self, width, height, st, at):
            r = renpy.Render(1920, 1080)
            lienzo = r.canvas()
            for cx, cy in self.centros.values():
                lienzo.circle((15, 23, 42, 150), (int(cx), int(cy)), 180)
                lienzo.circle((56, 189, 248, 70), (int(cx), int(cy)), 180, 2)
            for origen, destino, peso in self.grafo.aristas():
                if origen in self.posiciones and destino in self.posiciones:
                    lienzo.line((148, 163, 184, 28 + int(30 * peso)), self.posiciones[origen], self.posiciones[destino], 2)
            return r

    class VistaArcade(renpy.Displayable):

        def __init__(self, sim, titulo, rumor, **kwargs):
            super(VistaArcade, self).__init__(**kwargs)
            self.sim = sim
            self.titulo = titulo
            self.rumor = rumor
            self.rastreo = isinstance(sim, RastreoEnVivo)
            self.pos, self.centros = posiciones_mapa(sim.grafo, sim.inmunes)
            self.mapa = CapaMapa(sim.grafo, self.pos, self.centros)
            self.fondo = renpy.displayable(FONDO_RASTREADOR if self.rastreo else (FONDO_VIRALIZACION if sim.modo == "viral" else FONDO_CONTENCION))
            self.ultimo_st = None
            self.mouse = (960, 600)
            self.flotantes = []
            self.anillos = []
            self.banner = None
            self.sacudida = 0.0
            self.vistos = 0
            self.fin_avisado = False
            self.textos = {}
            self.avatares = {}
            self.dt = 0.0

        # ----- utilidades de dibujo -----

        def texto(self, contenido, size=20, color="#f8fafc", bold=False):
            clave = (contenido, size, color, bold)
            if clave not in self.textos:
                if len(self.textos) > 500:
                    self.textos.clear()
                self.textos[clave] = Text(contenido, size=size, color=color, bold=bold,
                                          outlines=[(2, "#000000c0", 0, 0)])
            return self.textos[clave]

        def avatar(self, nodo, lado, alfa=1.0):
            revelar = self.sim.estado_nodo.get(nodo) == "cuarentena" or (self.rastreo and nodo in self.sim.rastro)
            ruta = icono_aparente(self.sim.grafo, nodo, revelar)
            clave = (ruta, lado, alfa)
            if clave not in self.avatares:
                self.avatares[clave] = Transform(ruta, xysize=(lado, lado), alpha=alfa)
            return self.avatares[clave]

        def poner(self, r, disp, x, y, st, at, ancla=(0.5, 0.5)):
            rr = renpy.render(disp, 1920, 1080, st, at)
            r.blit(rr, (int(x - rr.width * ancla[0]), int(y - rr.height * ancla[1])))

        def pos_paquete(self, paquete, progreso=None):
            p = paquete.progreso if progreso is None else max(0.0, progreso)
            x1, y1 = self.pos[paquete.origen]
            x2, y2 = self.pos[paquete.destino]
            dx, dy = x2 - x1, y2 - y1
            largo = math.hypot(dx, dy) or 1
            ox, oy = (-dy / largo * 7, dx / largo * 7) if self.sim.grafo.existe_conexion(paquete.destino, paquete.origen) else (0, 0)
            return x1 + dx * p + ox, y1 + dy * p + oy

        def flotar(self, x, y, contenido, color, size=24, dur=1.1):
            self.flotantes.append([x, y, contenido, color, size, 0.0, dur])

        def anillo(self, x, y, color, radio_max, dur=0.5):
            self.anillos.append([x, y, color, radio_max, 0.0, dur])

        # ----- eventos de la simulacion -> efectos -----

        def consumir_eventos(self):
            eventos = self.sim.eventos[self.vistos:]
            self.vistos = len(self.sim.eventos)
            for ev in eventos:
                tipo = ev["tipo"]
                nodo = ev.get("nodo")
                x, y = self.pos.get(nodo, (960, 540))
                if tipo == "contagio":
                    self.flotar(x, y - 40, "+%s" % formato_num(ev["reposts"]), "#f87171")
                    self.anillo(x, y, "#ef4444", 80)
                    if self.sim.grafo.alcance(nodo) >= 30:
                        self.sacudida = 0.35
                    sonar(SONIDO_AVISO["malo"])
                elif tipo == "bloqueado":
                    self.flotar(x, y - 40, "BLOQUEADO", "#38bdf8", 20)
                elif tipo == "cuarentena":
                    self.flotar(x, y - 50, "CUARENTENA  -%s reposts" % formato_num(ev["evitados"]), "#7dd3fc", 22)
                    self.anillo(x, y, "#38bdf8", 140, 0.6)
                    sonar(SONIDO_AVISO["bueno"])
                elif tipo == "cuarentena_fin":
                    self.flotar(x, y - 40, "VUELVE A COMPARTIR", "#fb923c", 18)
                elif tipo == "foco":
                    self.flotar(x, y - 50, "NUEVO FOCO", "#ef4444", 24)
                    self.anillo(x, y, "#ef4444", 160, 0.8)
                elif tipo == "onda_lista":
                    self.flotar(1770, 160, "+1 ONDA", "#38bdf8", 22)
                elif tipo == "banner":
                    self.banner = [ev["titulo"], ev["texto"], ev["malo"], 0.0]
                    if ev["malo"]:
                        self.sacudida = 0.4
                        sonar(SONIDO_AVISO["alerta"])
                elif tipo == "rastro":
                    self.flotar(x, y - 50, "RASTRO +%d" % ev["puntos"], "#facc15", 26)
                    self.anillo(x, y, "#facc15", 120, 0.6)
                    sonar(SONIDO_AVISO["info"])
                elif tipo == "rastro_falso":
                    self.flotar(x, y - 50, "PISTA FALSA  -%ds" % self.sim.cfg["penalizacion_rastro"], "#f87171", 24)
                    self.sacudida = 0.3
                    sonar(SONIDO_AVISO["malo"])
                elif tipo == "pista":
                    self.anillo(x, y, "#ffffff", 150, 0.8)
                elif tipo == "fin":
                    sonar(SONIDO_EXITO if ev["exito"] else SONIDO_FALLO)

        # ----- render -----

        def render(self, width, height, st, at):
            dt = 0.0 if self.ultimo_st is None else max(0.0, min(0.05, st - self.ultimo_st))
            self.ultimo_st = st
            self.dt = dt
            if renpy.get_screen("debug_arcade") is None:
                self.sim.actualizar(dt)
            self.consumir_eventos()
            if self.sim.terminado() and not self.fin_avisado:
                renpy.timeout(0)

            for f in self.flotantes:
                f[5] += dt
                f[1] -= 40 * dt
            self.flotantes = [f for f in self.flotantes if f[5] < f[6]]
            for a in self.anillos:
                a[4] += dt
            self.anillos = [a for a in self.anillos if a[4] < a[5]]
            self.sacudida = max(0.0, self.sacudida - dt)

            r = renpy.Render(1920, 1080)
            self.poner(r, self.fondo, 0, 0, st, at, (0, 0))
            self.poner(r, Solid("#00000070"), 0, 0, st, at, (0, 0))

            ox = oy = 0
            if self.sacudida > 0:
                fuerza = 10 * self.sacudida
                ox, oy = random.uniform(-1, 1) * fuerza, random.uniform(-1, 1) * fuerza
            capa = renpy.Render(1920, 1080)
            self.dibujar_mundo(capa, st, at)
            r.blit(capa, (int(ox), int(oy)))

            v = self.sim.viralidad()
            if v >= 0.75 and not self.sim.terminado():
                alfa = int(40 + 50 * (0.5 + 0.5 * math.sin(st * 6)) * (v - 0.75) * 4)
                self.poner(r, Solid("#ff0000%02x" % min(120, alfa)), 0, 0, st, at, (0, 0))

            self.dibujar_hud(r, st, at)
            if self.sim.intro > 0:
                self.dibujar_intro(r, st, at)
            renpy.redraw(self, 0)
            return r

        def dibujar_mundo(self, r, st, at):
            sim = self.sim
            self.poner(r, self.mapa, 0, 0, st, at, (0, 0))
            for barrio, (cx, cy) in self.centros.items():
                self.poner(r, self.texto(barrio.upper(), 22, "#7dd3fc", True), cx, cy - 200, st, at)

            if self.rastreo:
                rastro = sim.rastro
                for i in range(len(rastro) - 1):
                    x1, y1 = self.pos[rastro[i]]
                    x2, y2 = self.pos[rastro[i + 1]]
                    largo = math.hypot(x2 - x1, y2 - y1)
                    haz = Transform(Solid("#facc15", xysize=(int(largo), 6)),
                                    rotate=math.degrees(math.atan2(y2 - y1, x2 - x1)))
                    self.poner(r, haz, (x1 + x2) / 2.0, (y1 + y2) / 2.0, st, at)

            for nodo, (x, y) in self.pos.items():
                self.dibujar_nodo(r, nodo, x, y, st, at)

            for paquete in sim.paquetes:
                for k, alfa in ((3, 0.15), (2, 0.3), (1, 0.5)):
                    gx, gy = self.pos_paquete(paquete, paquete.progreso - 0.035 * k)
                    self.poner(r, Transform(circulo("#fb923c", "#fb923c", 9), alpha=alfa), gx, gy, st, at)
                px, py = self.pos_paquete(paquete)
                urgente = paquete.progreso > 0.75
                self.poner(r, circulo("#ef4444" if urgente else "#f97316", "#fde68a", 14), px, py, st, at)

            for x, y, color, radio_max, edad, dur in self.anillos:
                t = edad / dur
                self.poner(r, Transform(aro(color, 10 + radio_max * t), alpha=1.0 - t), x, y, st, at)

            for x, y, contenido, color, size, edad, dur in self.flotantes:
                self.poner(r, Transform(self.texto(contenido, size, color, True), alpha=max(0.0, 1.0 - edad / dur)), x, y, st, at)

            if sim.ondas > 0 and sim.jugando():
                self.poner(r, Transform(aro("#38bdf8", sim.cfg["radio_onda"], 2), alpha=0.12), self.mouse[0], self.mouse[1], st, at)
            self.poner(r, aro("#f8fafc", 22, 2), self.mouse[0], self.mouse[1], st, at)

            if self.banner:
                titulo, texto, malo, edad = self.banner
                self.banner[3] += self.dt
                if edad > 2.6:
                    self.banner = None
                else:
                    alfa = min(1.0, edad * 5, (2.6 - edad) * 3)
                    zoom = 1.0 + max(0.0, 0.4 - edad * 2)
                    caja = Solid("#7f1d1df0" if malo else "#14532df0", xysize=(1100, 140))
                    self.poner(r, Transform(caja, alpha=alfa), 960, 520, st, at)
                    self.poner(r, Transform(self.texto(titulo, 50, "#ffffff", True), alpha=alfa, zoom=zoom), 960, 500, st, at)
                    self.poner(r, Transform(self.texto(texto, 24, "#f1f5f9"), alpha=alfa), 960, 560, st, at)

        def dibujar_nodo(self, r, nodo, x, y, st, at):
            sim = self.sim
            estado = sim.estado_nodo[nodo]
            radio = radio_arcade(sim.grafo, nodo)
            color = COLOR_ARCADE.get(estado, "#475569")
            pulso = 1.0
            if estado == "infectado":
                pulso = 1.0 + 0.07 * math.sin(st * 7 + x)
                if self.rastreo:
                    color = color_edad(sim.edad(nodo))
            if self.rastreo and nodo in sim.rastro:
                color = COLOR_ARCADE["rastro"]
                if nodo == sim.actual():
                    pulso = 1.0 + 0.12 * math.sin(st * 8)
            dibujo = int(radio * pulso)
            self.poner(r, circulo(color, aclarar(color, 60), dibujo), x, y, st, at)
            alfa = 0.55 if (self.rastreo and nodo not in sim.hora) else 1.0
            self.poner(r, self.avatar(nodo, (radio - 6) * 2, alfa), x, y, st, at)

            if math.hypot(self.mouse[0] - x, self.mouse[1] - y) <= radio + 6 and sim.jugando():
                self.poner(r, aro("#ffffff", radio + 6, 3), x, y, st, at)
            if self.rastreo:
                if nodo == sim.actual() and sim.jugando():
                    self.poner(r, aro("#facc15", radio + 14, 3), x, y, st, at)
                if nodo == sim.pista_nodo and sim.transcurrido < sim.pista_hasta and int(st * 6) % 2 == 0:
                    self.poner(r, aro("#ffffff", radio + 16, 5), x, y, st, at)
                if nodo == sim.inicio:
                    self.poner(r, self.texto("PUBLICACION VIRAL", 15, "#fca5a5", True), x, y - radio - 16, st, at)
            if estado == "cuarentena" and nodo in sim.fin_cuarentena:
                restante = int(sim.fin_cuarentena[nodo] - sim.transcurrido) + 1
                self.poner(r, self.texto("%ds" % restante, 18, "#7dd3fc", True), x, y - radio - 14, st, at)
            self.poner(r, self.texto(sim.grafo.nombre(nodo), 15, "#e2e8f0"), x, y + radio + 12, st, at)

        def dibujar_hud(self, r, st, at):
            sim = self.sim
            self.poner(r, Solid("#020617e8", xysize=(1920, 150)), 0, 0, st, at, (0, 0))
            self.poner(r, self.texto(self.titulo, 40, "#facc15" if self.rastreo else "#f87171", True), 40, 18, st, at, (0, 0))
            if self.rastreo:
                objetivo = "Sigue el rastro hasta la cuenta que INICIO el rumor"
                controles = "CLIC cuenta: seguir rastro  -  CLIC DERECHO: retroceder  -  H: pista (-%ds)  -  CLIC rumor: frenarlo  -  ESPACIO: onda" % sim.cfg["costo_pista"]
            else:
                objetivo = "Revienta los rumores antes de que lleguen a mas cuentas"
                controles = "CLIC rumor en vuelo: interceptar  -  CLIC cuenta roja: cuarentena  -  ESPACIO: onda de verificacion"
            self.poner(r, self.texto(objetivo, 21, "#f8fafc", True), 40, 72, st, at, (0, 0))
            self.poner(r, self.texto(controles, 16, "#94a3b8"), 40, 108, st, at, (0, 0))

            v = sim.viralidad()
            color_v = "#ef4444" if v >= 0.75 else ("#f59e0b" if v >= 0.5 else "#22c55e")
            self.poner(r, self.texto("VIRALIDAD  %d%%" % int(v * 100), 18, color_v, True), 1010, 18, st, at, (0, 0))
            self.poner(r, Solid("#1e293b", xysize=(300, 26)), 1010, 46, st, at, (0, 0))
            if v > 0:
                self.poner(r, Solid(color_v, xysize=(max(1, int(300 * v)), 26)), 1010, 46, st, at, (0, 0))
            self.poner(r, self.texto("%s reposts" % formato_num(sim.reposts), 18, "#cbd5e1"), 1010, 80, st, at, (0, 0))

            segundos = int(math.ceil(sim.tiempo_restante()))
            self.poner(r, self.texto("TIEMPO", 16, "#94a3b8"), 1350, 18, st, at, (0, 0))
            self.poner(r, self.texto("%d:%02d" % (segundos // 60, segundos % 60), 44,
                                     "#ef4444" if segundos <= 10 else "#f8fafc", True), 1350, 40, st, at, (0, 0))

            self.poner(r, self.texto("PUNTOS", 16, "#94a3b8"), 1510, 18, st, at, (0, 0))
            self.poner(r, self.texto(formato_num(sim.puntos), 36, "#f8fafc", True), 1510, 40, st, at, (0, 0))
            if sim.combo >= 2:
                self.poner(r, self.texto("COMBO x%d" % sim.combo, 22 + sim.combo * 2, "#facc15", True), 1510, 88, st, at, (0, 0))

            self.poner(r, self.texto("ONDAS", 16, "#94a3b8"), 1720, 18, st, at, (0, 0))
            for i in range(sim.cfg["max_ondas"]):
                color_o = "#38bdf8" if i < sim.ondas else "#1e293b"
                self.poner(r, circulo(color_o, aclarar(color_o, 50), 12), 1732 + i * 32, 56, st, at)
            if self.rastreo:
                estado = "RASTRO: %d cuentas" % len(sim.rastro)
                color_e = "#facc15"
            elif sim.cooldown > 0:
                estado = "CUARENTENA %.1fs" % sim.cooldown
                color_e = "#64748b"
            else:
                estado = "CUARENTENA LISTA"
                color_e = "#38bdf8"
            self.poner(r, self.texto(estado, 16, color_e, True), 1720, 82, st, at, (0, 0))
            self.poner(r, self.texto("\"" + self.rumor + "\"", 17, "#fca5a5"), 960, 1062, st, at)

            if self.rastreo:
                self.poner(r, self.texto("Color del contagio:", 15, "#cbd5e1"), 40, 1000, st, at, (0, 0))
                for i in range(8):
                    c = mezclar("#f97316", "#7e22ce", i / 7.0)
                    self.poner(r, circulo(c, c, 9), 200 + i * 24, 1010, st, at)
                self.poner(r, self.texto("reciente  ->  antiguo", 15, "#cbd5e1"), 400, 1000, st, at, (0, 0))

        def dibujar_intro(self, r, st, at):
            self.poner(r, Solid("#000000c0"), 0, 0, st, at, (0, 0))
            numero = int(math.ceil(self.sim.intro))
            self.poner(r, self.texto(self.titulo, 64, "#facc15" if self.rastreo else "#f87171", True), 960, 300, st, at)
            if self.rastreo:
                lineas = ["El rumor ya se esta extendiendo. Encuentra quien lo empezo.",
                          "Haz clic en la cuenta que se lo envio a la cuenta amarilla.",
                          "Pista: los colores mas MORADOS lo compartieron hace mas tiempo."]
            else:
                lineas = ["Los rumores viajan como bolas de fuego entre cuentas.",
                          "Haz CLIC sobre ellos para reventarlos antes de que lleguen.",
                          "CLIC en una cuenta roja = cuarentena.   ESPACIO = onda que limpia el area."]
            for i, linea in enumerate(lineas):
                self.poner(r, self.texto(linea, 28, "#f8fafc"), 960, 420 + i * 50, st, at)
            self.poner(r, self.texto(str(numero), 140, "#ffffff", True), 960, 720, st, at)

        # ----- entrada -----

        def event(self, ev, x, y, st):
            if ev.type == pygame.MOUSEMOTION:
                self.mouse = (x, y)
            if self.sim.terminado():
                if not self.fin_avisado:
                    self.fin_avisado = True
                    renpy.restart_interaction()
                return None
            if renpy.get_screen("debug_arcade") is not None:
                return None
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self.mouse = (x, y)
                if ev.button == 1:
                    self.clic(x, y)
                elif ev.button == 3 and self.rastreo:
                    self.sim.volver()
                raise renpy.IgnoreEvent()
            if ev.type == pygame.MOUSEBUTTONUP and ev.button in (1, 3, 4, 5):
                raise renpy.IgnoreEvent()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    self.lanzar_onda()
                    raise renpy.IgnoreEvent()
                if ev.key == pygame.K_h and self.rastreo:
                    self.sim.pedir_pista()
                    raise renpy.IgnoreEvent()
            return None

        def clic(self, x, y):
            sim = self.sim
            if not sim.jugando():
                return
            mejor, distancia = None, 42
            for paquete in sim.paquetes:
                px, py = self.pos_paquete(paquete)
                d = math.hypot(px - x, py - y)
                if d < distancia:
                    mejor, distancia = paquete, d
            if mejor is not None:
                ganados = sim.interceptar(mejor)
                self.flotar(x, y - 20, "+%d" % ganados, "#fde68a", 22 + 3 * sim.combo, 0.8)
                if sim.combo >= 2:
                    self.flotar(x, y - 50, "x%d" % sim.combo, "#facc15", 30, 0.8)
                self.anillo(x, y, "#fde68a", 50, 0.3)
                sonar(SONIDO_INTERCEPCION)
                return
            for nodo, (nx, ny) in self.pos.items():
                if math.hypot(nx - x, ny - y) <= radio_arcade(sim.grafo, nodo) + 6:
                    if self.rastreo:
                        sim.rastrear(nodo)
                    elif not sim.cuarentena(nodo):
                        motivo = "ESPERA %.1fs" % sim.cooldown if sim.cooldown > 0 else "NO ESTA COMPARTIENDO"
                        self.flotar(nx, ny - 40, motivo, "#94a3b8", 18, 0.7)
                    return
            self.anillo(x, y, "#64748b", 30, 0.25)

        def lanzar_onda(self):
            sim = self.sim
            if not sim.jugando() or sim.ondas <= 0:
                return
            x, y = self.mouse
            radio = sim.cfg["radio_onda"]
            dentro = [p for p in sim.paquetes if math.hypot(self.pos_paquete(p)[0] - x, self.pos_paquete(p)[1] - y) <= radio]
            eliminados = sim.onda(dentro)
            self.anillo(x, y, "#38bdf8", radio, 0.5)
            self.flotar(x, y - 30, "ONDA  -%d rumores" % eliminados, "#7dd3fc", 28, 1.0)
            sonar(SONIDO_AVISO["bueno"])


screen arcade_ui(sim, titulo, rumor):
    modal True
    zorder 40
    default vista = VistaArcade(sim, titulo, rumor)
    add vista

    if modo_sustentacion and not sim.terminado():
        textbutton "RED INTERNA":
            style "grafo_button"
            text_style "grafo_button_text"
            xpos 1740
            ypos 165
            xsize 160
            action Show("debug_arcade", sim=sim)

    if sim.terminado():
        use resultado_arcade(sim)


transform nota_golpe:
    zoom 3.0 alpha 0.0
    easein 0.35 zoom 1.0 alpha 1.0

screen resultado_arcade(sim):
    zorder 100
    $ nota = sim.calificacion()
    $ color_nota = {"S": "#facc15", "A": "#22c55e", "B": "#38bdf8", "C": "#a78bfa", "D": "#ef4444"}[nota]
    add Solid("#000000b0")
    frame:
        align (0.5, 0.5)
        xsize 980
        background ("#0b1324f5")
        padding (50, 36)
        vbox:
            spacing 12
            xfill True
            text ("VICTORIA" if sim.exito() else "DERROTA") size 60 bold True color ("#22c55e" if sim.exito() else "#ef4444") xalign 0.5
            text nota size 160 bold True color color_nota xalign 0.5 at nota_golpe
            text sim.motivo_fin size 24 color "#f1f5f9" xalign 0.5 textalign 0.5
            null height 6
            hbox:
                xalign 0.5
                spacing 50
                vbox:
                    text "PUNTOS" size 16 color "#94a3b8" xalign 0.5
                    text formato_num(sim.puntos) size 34 bold True color "#f8fafc" xalign 0.5
                vbox:
                    text "INTERCEPTADOS" size 16 color "#94a3b8" xalign 0.5
                    text "[sim.interceptados]" size 34 bold True color "#f8fafc" xalign 0.5
                vbox:
                    text "MEJOR COMBO" size 16 color "#94a3b8" xalign 0.5
                    text "x[sim.mejor_combo]" size 34 bold True color "#facc15" xalign 0.5
                vbox:
                    text "REPOSTS" size 16 color "#94a3b8" xalign 0.5
                    text formato_num(sim.reposts) size 34 bold True color "#f87171" xalign 0.5
            null height 10
            textbutton "CONTINUAR":
                style "grafo_button"
                text_style "grafo_button_text"
                xalign 0.5
                xsize 360
                text_xalign 0.5
                action Return()


label jugar_arcade(sim, titulo, rumor):
    $ hud_estaba_visible = renpy.get_screen("hud_ciudad") is not None
    $ ocultar_avisos_juego()
    hide screen hud_ciudad
    $ quick_menu_previo = quick_menu
    $ quick_menu = False
    window hide
    $ renpy.block_rollback()
    call screen arcade_ui(sim, titulo, rumor)
    $ quick_menu = quick_menu_previo
    if hud_estaba_visible:
        show screen hud_ciudad
    $ renpy.block_rollback()
    return
