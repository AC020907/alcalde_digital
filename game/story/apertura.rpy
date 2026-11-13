## Apertura cinematografica «Ciudad Nova en crisis» (Feria Gamer). Guia de direccion: docs/APERTURA_FERIA_GAMER.md.
## Calma -> incertidumbre -> crisis -> decision -> consecuencia -> accion -> titulo.
## El movimiento sale de tres piezas: ATL sobre las ilustraciones del equipo, la camara de Ren'Py en el
## despacho y CiudadRumor, que mueve una camara sobre el mapa ilustrado y dibuja la propagacion REAL (BFS de
## red_civitas) con el mismo trazo plano de los sprites: tinta oscura, colores de la paleta, sin brillos.

default apertura_decision = None
default apertura_micro = None
default apertura_tiempos = {}
default apertura_antes = {}

init -1 python:
    import math as _ap_math
    import time as _apertura_time
    from clases.Publicacion import Publicacion

    # ---------- Paleta (la misma de la interfaz y los sprites) ----------
    AP_TINTA = "#2b2440"       # trazo y texto
    AP_PAPEL = "#fbf6ee"       # tarjetas
    AP_RUMOR = "#d1495b"       # lo que propaga el rumor
    AP_FRENO = "#3d7ea6"       # cuentas frenadas por tu respuesta
    AP_NOCHE = "#120d1c"       # fondos y veladuras
    AP_VINO = "#8c2f4b"        # acento de la marca
    AP_LILA = "#c9b8d8"        # texto secundario sobre oscuro
    AP_FUENTE_FINA = "fonts/Roboto-Light.ttf"
    # En la web (emscripten) el canvas se dibuja por software: 15 cuadros/s bastan y no bloquean el navegador.
    AP_REFRESCO = (1.0 / 15) if renpy.emscripten else 0

    # Centro de cada zona de la red sobre images/bg/mapa.jpg (3072 x 2048).
    MAPA_ZONAS = {"Norte": (560, 640), "Centro": (1480, 780), "Medios": (2140, 560),
                  "Alcaldia": (1830, 1110), "Oeste": (760, 1380), "Sur": (1480, 1740)}

    def ap_suave(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3 - 2 * x)

    def ap_posiciones_mapa(red):
        """Cuentas agrupadas por barrio alrededor de su zona del mapa (espiral de Fermat: no se solapan)."""
        pos, cuenta = {}, {}
        for n in sorted(red.lista_nodos()):
            zona = red.perfil(n).get("barrio", "Centro")
            k = cuenta.get(zona, 0)
            cuenta[zona] = k + 1
            cx, cy = MAPA_ZONAS.get(zona, (1500, 1000))
            if zona == "Alcaldia":
                pos[n] = (cx, cy)
                continue
            ang = k * 2.39996 + 0.5
            radio = 95 + 62 * _ap_math.sqrt(k)
            pos[n] = (cx + radio * _ap_math.cos(ang) * 1.2, cy + radio * _ap_math.sin(ang) * 0.85)
        return pos

    class CiudadRumor(renpy.Displayable):
        """Camara sobre el mapa de Ciudad Nova + propagacion por niveles de un BFS ya calculado.

        camara: [(t, x, y, zoom), ...] en coordenadas del mapa; entre claves se interpola con suavizado.
        niveles/padres: salida de GrafoSocial.bfs_propagacion. Cada nivel tarda `paso` segundos:
        la arista crece desde quien lo envia y el nodo se marca al llegar.
        """
        MAPA = "images/bg/mapa.jpg"

        def __init__(self, red, niveles, padres, camara, inicio=0.0, paso=0.55, bloqueados=(),
                     velo=0.35, etiquetas=True, **kw):
            super(CiudadRumor, self).__init__(**kw)
            self.red, self.niveles, self.padres = red, niveles, padres
            self.camara, self.inicio, self.paso = camara, inicio, paso
            self.bloqueados = set(bloqueados)
            self.velo = velo
            self.etiquetas = etiquetas
            self.pos = ap_posiciones_mapa(red)
            self.nivel_de = {n: i for i, nivel in enumerate(niveles) for n in nivel}
            self.forzado = False
            self.fin = inicio + paso * max(1, len(niveles)) + 0.2
            self.reducido = bool(persistent.reducir_movimiento)

        def terminar(self):
            self.forzado = True
            renpy.redraw(self, 0)

        def cam(self, t):
            x, y, z = self._cam(t)
            z = max(z, 1920.0 / 3072, 1080.0 / 2048)
            x = max(960.0 / z, min(3072 - 960.0 / z, x))
            y = max(540.0 / z, min(2048 - 540.0 / z, y))
            return x, y, z

        def _cam(self, t):
            claves = self.camara
            if self.forzado:
                return claves[-1][1:]
            if t <= claves[0][0]:
                return claves[0][1:]
            for a, b in zip(claves, claves[1:]):
                if t <= b[0]:
                    if self.reducido:
                        return a[1:]
                    s = ap_suave((t - a[0]) / max(0.001, b[0] - a[0]))
                    return tuple(a[i] + (b[i] - a[i]) * s for i in (1, 2, 3))
            return claves[-1][1:]

        def progreso(self, nodo, t):
            """0..1: cuanto ha avanzado la llegada del rumor a este nodo."""
            if nodo not in self.nivel_de:
                return 0.0
            if self.forzado:
                return 1.0
            nivel = self.nivel_de[nodo]
            if nivel == 0:
                return 1.0 if t >= self.inicio else 0.0
            p = (t - self.inicio - (nivel - 1) * self.paso) / self.paso
            if self.reducido:
                return 1.0 if p >= 1.0 else 0.0
            return max(0.0, min(1.0, p))

        def alcanzados(self, t):
            return sum(1 for n, nivel in self.nivel_de.items() if nivel > 0 and self.progreso(n, t) >= 1.0)

        def render(self, width, height, st, at):
            r = renpy.Render(width, height)
            # Hasta que su plano empieza no se dibuja nada (en la web el canvas es por software y costoso).
            if not self.forzado and st < self.camara[0][0] - 0.3:
                renpy.redraw(self, max(0.05, self.camara[0][0] - 0.3 - st))
                return r
            cx, cy, z = self.cam(st)
            ox, oy = width / 2.0 - cx * z, height / 2.0 - cy * z
            r.blit(renpy.render(Transform(self.MAPA, zoom=z), width, height, st, at), (int(ox), int(oy)))
            if self.velo:
                r.blit(renpy.render(Transform(Solid(AP_NOCHE), alpha=self.velo), width, height, st, at), (0, 0))
            c = r.canvas()
            esc = max(0.95, min(1.5, z / 0.75))

            def sp(n):
                x, y = self.pos[n]
                return (int(ox + x * z), int(oy + y * z))

            # Aristas: primero tinta y encima el color (trazo de dos tonos, como el lineart de los sprites).
            for n, padre in self.padres.items():
                p = self.progreso(n, st)
                if p <= 0 or padre not in self.pos or n not in self.pos:
                    continue
                a, b = sp(padre), sp(n)
                fin = (int(a[0] + (b[0] - a[0]) * p), int(a[1] + (b[1] - a[1]) * p))
                c.line(AP_TINTA, a, fin, int(8 * esc))
                c.line(AP_RUMOR, a, fin, int(4 * esc))
            for n in self.pos:
                x, y = sp(n)
                if x < -40 or y < -40 or x > width + 40 or y > height + 40:
                    continue
                radio = int((17 if n == "jugador" else 12) * esc)
                if n in self.bloqueados and (self.forzado or st >= self.inicio + self.paso):
                    relleno = AP_FRENO
                elif self.progreso(n, st) >= 1.0:
                    relleno = AP_TINTA if self.nivel_de.get(n) == 0 else AP_RUMOR
                else:
                    relleno = AP_PAPEL
                c.circle(AP_TINTA, (x, y), radio + max(2, int(3 * esc)))
                c.circle(relleno, (x, y), radio)
            if self.etiquetas:
                for n, texto in ((APERTURA_ORIGEN, "@verdad.oculta"), ("jugador", "Alcaldía")):
                    if n in self.pos:
                        x, y = sp(n)
                        t = renpy.render(Text(texto, size=22, bold=True, color=AP_PAPEL,
                                              outlines=[(3, AP_TINTA, 0, 0)]), width, height, st, at)
                        r.blit(t, (x - t.width // 2, y + int(18 * esc)))
            if not self.forzado and (st < self.fin or st < self.camara[-1][0]):
                renpy.redraw(self, AP_REFRESCO)
            return r

        def texto_alcance(self, st, at):
            n = self.alcanzados(st)
            return Text("%d" % n, size=64, bold=True, color=AP_RUMOR if n > 12 else AP_TINTA), 0.05

    class TituloRed(renpy.Displayable):
        """Logo de Civitas: cada letra es un nodo de la red. La arista llega, el punto se marca y la letra sube."""
        LETRAS = "CIVITAS"

        def __init__(self, tam=156, **kw):
            super(TituloRed, self).__init__(**kw)
            self.tam = tam
            self.paso = 0.16
            self.reducido = bool(persistent.reducir_movimiento)

        def letra(self, l):
            return Text(l, font=AP_FUENTE_FINA, size=self.tam, color=AP_PAPEL)

        def render(self, width, height, st, at):
            r = renpy.Render(width, height)
            medidas = [renpy.render(self.letra(l), width, height, st, at) for l in self.LETRAS]
            hueco = int(self.tam * 0.17)
            x = (width - sum(m.width for m in medidas) - hueco * (len(medidas) - 1)) // 2
            base = int(height * 0.52)
            centros = []
            for i, m in enumerate(medidas):
                centros.append(x + m.width // 2)
                p = 1.0 if self.reducido else ap_suave((st - (0.35 + i * self.paso)) / 0.35)
                if p > 0:
                    sube = 0 if self.reducido else int((1 - p) * 18)
                    img = renpy.render(Transform(self.letra(self.LETRAS[i]), alpha=p), width, height, st, at)
                    r.blit(img, (x, base - m.height + sube))
                x += m.width + hueco
            c = r.canvas()
            linea = base + 30
            for i, cx in enumerate(centros):
                t0 = 0.35 + i * self.paso
                if i > 0:
                    p = 1.0 if self.reducido else max(0.0, min(1.0, (st - (t0 - self.paso)) / self.paso))
                    if p > 0:
                        a = centros[i - 1]
                        c.line(AP_LILA, (a, linea), (int(a + (cx - a) * p), linea), 3)
            for i, cx in enumerate(centros):
                if self.reducido or st >= 0.35 + i * self.paso:
                    c.circle(AP_TINTA, (cx, linea), 11)
                    c.circle(AP_RUMOR if i == 0 else AP_PAPEL, (cx, linea), 7)
            if not self.reducido and st < 0.35 + len(self.LETRAS) * self.paso + 0.5:
                renpy.redraw(self, AP_REFRESCO)
            return r

init python:
    # Lo que cada respuesta hace con el rumor dentro del grafo (ver apertura_propagacion):
    # - desmentir: quienes siguen a la alcaldia leen el desmentido y no lo reenvian (vecinos bloqueados);
    # - analisis: los medios esperan los datos antes de repetir nada, pero el rumor sigue corriendo;
    # - ignorar: sin respuesta, cada cuenta lo reenvia con mas fuerza.
    APERTURA_SEMILLA = "apertura"
    APERTURA_ORIGEN = "@verdad.oculta"
    APERTURA_MEDIOS = ("@salud.nova", "@investigador.nova", "@noticias.nova")
    APERTURA_RESPUESTA = {
        "desmentir": {"titulo": "Desmentiste sin datos", "consecuencia": {"confianza": 2, "info_verificada": -2},
                      "texto": "Quienes te siguen leen el desmentido y frenan el rumor. Pero no hay ningún análisis detrás.",
                      "voz": ("@vecina.ana", "La alcaldía dice que es 100% segura. ¿Con qué análisis?")},
        "analisis": {"titulo": "Pediste los análisis", "consecuencia": {"info_verificada": 3, "desinformacion": 2},
                     "texto": "Los medios esperan los datos antes de repetir nada. Mientras tanto, el rumor sigue corriendo.",
                     "voz": ("@noticias.nova", "La alcaldía pidió los análisis del agua. Informaremos con datos.")},
        "ignorar": {"titulo": "No interviniste", "consecuencia": {"desinformacion": 4, "confianza": -2},
                    "texto": "Sin una respuesta de la alcaldía, cada cuenta lo reenvía con más fuerza.",
                    "voz": ("@preocupado99", "¿Y el alcalde? ¿Nadie va a decir nada? Yo ya no tomo agua.")},
    }

    # Comentarios propios de la microprueba: no estan en el banco de Moderacion Express (no se repiten luego).
    COMENTARIOS_APERTURA = [
        ("@aguasegura_YA_77", "NO TOMEN AGUA DEL GRIFO. La alcaldía lo sabía desde ayer. COMPARTE", True),
        ("@rosa.del.sur", "Mi bebé toma tetero con agua de la llave. ¿Alguien sabe algo oficial?", False),
        ("@despierta_nova_x", "#AguaEnvenenada #AguaEnvenenada #AguaEnvenenada RT RT RT", True),
        ("@hector.taxi", "Alcalde, usted nunca responde a tiempo. Esta vez dé la cara.", False),
    ]

    def apertura_marca(nombre):
        """Tiempos de la apertura (segundos desde que empieza). Sin datos personales."""
        t = _apertura_time.time()
        if "_t0" not in store.apertura_tiempos or nombre == "inicio":
            store.apertura_tiempos = {"_t0": t}
        store.apertura_tiempos[nombre] = round(t - store.apertura_tiempos["_t0"], 1)

    def apertura_propagacion(eleccion):
        """BFS real sobre red_civitas desde la cuenta que inventa el rumor; depende de la respuesta del jugador."""
        red = store.red_civitas
        if eleccion == "desmentir":
            bloqueados, factor = set(red.vecinos("jugador")), 1.0
        elif eleccion == "analisis":
            bloqueados, factor = set(APERTURA_MEDIOS), 1.0
        elif eleccion == "ignorar":
            bloqueados, factor = set(), 1.35
        else:                                   # montaje: el rumor antes de que nadie responda
            bloqueados, factor = set(), 1.0
        padres = {}
        niveles = red.bfs_propagacion(APERTURA_ORIGEN, semilla=APERTURA_SEMILLA, factor=factor,
                                      bloqueados=bloqueados, padres=padres)
        return niveles, padres, bloqueados

    def apertura_decidir(eleccion):
        """Aplica la decision del prologo una sola vez (rollback y reintentos no la repiten)."""
        if store.apertura_decision is not None:
            return False
        store.apertura_antes = {k: getattr(store.ciudad, k) for k in ("confianza", "desinformacion", "info_verificada")}
        store.apertura_decision = eleccion
        if eleccion == "desmentir":
            hecho("desmintio_sin_datos")
            calidad_decision("prologo_agua", 0.4)
        elif eleccion == "analisis":
            hecho("pidio_analisis")
            calidad_decision("prologo_agua", 1.0)
            subir_afinidad("claudia", 1)
        else:
            hecho("ignoro_rumor_agua")
            calidad_decision("prologo_agua", 0.0)
            subir_afinidad("claudia", -1)
        aplicar_consecuencia(APERTURA_RESPUESTA[eleccion]["consecuencia"])
        renpy.hide_screen("cambios_indicadores")
        return True

    def apertura_micro_resultado(cola):
        """Consecuencia de la microprueba: una vez, y sin tocar el registro del Moderacion Express completo."""
        if store.apertura_micro is not None:
            return store.apertura_micro
        censuro = any(eliminar and not p.es_falsa for p, eliminar, _ok in cola.historial)
        bots_quedaron = any((not eliminar) and p.es_falsa for p, eliminar, _ok in cola.historial)
        if not cola.historial:
            r = "sin_jugar"
        elif censuro:
            r = "censuro"
            aplicar_consecuencia({"convivencia": -1})
        elif bots_quedaron:
            r = "bots"
            aplicar_consecuencia({"desinformacion": 1})
        else:
            r = "limpio"
            aplicar_consecuencia({"confianza": 1})
        store.apertura_micro = r
        return r

    def apertura_montaje_vista():
        niveles, padres, _b = apertura_propagacion(None)
        # El rumor nace en Barrio Norte, la camara se abre mientras la ciudad se llena y baja hasta la Alcaldia.
        camara = [(8.3, 560, 640, 1.25), (9.4, 600, 660, 1.1), (13.0, 1460, 1060, 0.6),
                  (14.4, 1700, 1080, 0.82), (15.4, 1830, 1110, 1.5)]
        return CiudadRumor(red_civitas, niveles, padres, camara, inicio=9.2, paso=0.62, velo=0.42)

    def apertura_reaccion_vista(niveles, padres, bloqueados):
        camara = [(0.0, 620, 700, 1.0), (0.6, 640, 720, 0.95), (3.6, 1420, 1080, 0.6)]
        return CiudadRumor(red_civitas, niveles, padres, camara, inicio=0.5, paso=0.5,
                           bloqueados=bloqueados, velo=0.45)


## ---------------- Transformaciones (entradas y cortes 0,3-0,6 s; camara 6-9 s) ----------------
transform ap_aparece(retraso, dx=0, dy=14):
    alpha 0.0 xoffset (0 if persistent.reducir_movimiento else dx) yoffset (0 if persistent.reducir_movimiento else dy)
    pause retraso
    easein 0.4 alpha 1.0 xoffset 0 yoffset 0

transform ap_se_va(retraso):
    pause retraso
    linear 0.35 alpha 0.0

transform ap_plano_ciudad:
    # Amanecer: la camara avanza despacio sobre la ciudad dormida.
    xalign 0.2 yalign 0.6 zoom (1.0 if persistent.reducir_movimiento else 1.14)
    linear (0.1 if persistent.reducir_movimiento else 9.0) xalign 0.55 zoom (1.0 if persistent.reducir_movimiento else 1.05)

transform ap_velo(desde, hasta, retraso, dur):
    alpha desde
    pause retraso
    linear dur alpha hasta

transform ap_toast(retraso):
    alpha 0.0 xoffset (0 if persistent.reducir_movimiento else 60)
    pause retraso
    easeout 0.35 alpha 1.0 xoffset 0

transform ap_primer_plano(retraso):
    # La publicacion llega desde la esquina de las notificaciones hasta el centro (silencio), y se hunde
    # en el mapa donde nacio el rumor.
    alpha 0.0 zoom (1.0 if persistent.reducir_movimiento else 0.45) xalign 0.92 yalign 0.08
    pause retraso
    easein 0.55 alpha 1.0 zoom 1.0 xalign 0.5 yalign 0.42
    pause 1.5
    easeout 0.5 zoom (1.0 if persistent.reducir_movimiento else 0.08) alpha 0.0 xalign 0.5 yalign 0.5

transform ap_inserto(retraso, giro):
    alpha 0.0 rotate giro yoffset (0 if persistent.reducir_movimiento else 30)
    pause retraso
    easeout 0.35 alpha 1.0 yoffset 0
    pause 1.6
    easein 0.3 alpha 0.0 yoffset (0 if persistent.reducir_movimiento else -12)

transform ap_revela_despacho:
    # Del edificio de la Alcaldia en el mapa al despacho: entra cerca del escritorio y se abre el plano.
    zoom (1.0 if persistent.reducir_movimiento else 1.22) xalign 0.62 yalign 0.55
    easeout (0.1 if persistent.reducir_movimiento else 2.4) zoom 1.0

transform ap_entra_lado:
    xoffset (0 if persistent.reducir_movimiento else 120) alpha 0.0
    easeout 0.5 xoffset 0 alpha 1.0

transform ap_acercar(z=1.06):
    # Acercamiento de camara para una linea importante (statement camera).
    xanchor 0.5 yanchor 0.42 xpos 0.5 ypos 0.42
    easein (0.01 if persistent.reducir_movimiento else 1.2) zoom (1.0 if persistent.reducir_movimiento else z)

transform ap_al_telefono:
    zoom 1.0 alpha 1.0 align (0.5, 0.5)
    pause 0.25
    easein 0.45 zoom (1.0 if persistent.reducir_movimiento else 3.0) alpha 0.0

style ap_marca is default:
    font AP_FUENTE_FINA
    size 22
    color AP_LILA
    kerning 8

## ---------------- Escenas 1-2: la ciudad, la notificacion, el rumor en el mapa (~15 s) ----------------
screen apertura_montaje():
    modal True
    default vista = apertura_montaje_vista()
    add Solid(AP_NOCHE)
    # Calma.
    add "bg panorama" at ap_plano_ciudad
    add Solid(AP_NOCHE) at ap_velo(0.75, 0.0, 0.0, 3.0)
    add Solid(AP_NOCHE) at ap_velo(0.0, 0.8, 6.3, 0.5)
    vbox at ap_aparece(0.9), ap_se_va(6.0):
        pos (88, 930)
        text "CIUDAD NOVA" style "ap_marca" size 30 color AP_PAPEL
        text "lunes · 6:09 a. m. · seis días antes de las elecciones" style "ap_marca" kerning 2

    # La primera notificacion; despues, otras.
    for i, (quien, texto, t) in enumerate((("@verdad.oculta", "El agua de Ciudad Nova está contaminada. No la tomen.", 3.2),
                                            ("Civitas", "12 personas que sigues lo compartieron", 4.4),
                                            ("Civitas", "340 reposts en 10 minutos", 5.2))):
        frame at ap_toast(t), ap_se_va(6.3):
            xpos 1300 ypos 60 + i * 112
            xsize 560
            background Solid(AP_PAPEL)
            padding (0, 0)
            hbox:
                add Solid(AP_RUMOR, xsize=8, ysize=96)
                vbox:
                    xoffset 18 yalign 0.5
                    text "CIVITAS  ·  %s" % quien size 16 bold True color AP_VINO kerning 1
                    text texto size 22 color AP_TINTA

    # Primer plano de la publicacion, en silencio.
    frame at ap_primer_plano(6.3):
        xsize 1180
        background Solid(AP_PAPEL)
        padding (56, 44)
        vbox:
            spacing 14
            text "@verdad.oculta  ·  Barrio Norte  ·  cuenta creada ayer" size 22 color "#8b84a8"
            text "El agua de Ciudad Nova está contaminada.\nNo la tomen. Compartan antes de que lo borren." size 50 bold True color AP_TINTA line_spacing 6

    # El rumor corre por la ciudad (BFS real) y la camara baja hasta la Alcaldia.
    add vista at ap_velo(0.0, 1.0, 8.3, 0.4)
    frame at ap_aparece(9.6, 0, 0), ap_se_va(14.6):
        xalign 0.97 ypos 60
        background Solid(AP_PAPEL)
        padding (26, 14)
        vbox:
            text "CUENTAS QUE YA LO COMPARTEN" size 15 bold True color AP_VINO kerning 3
            add DynamicDisplayable(vista.texto_alcance)
    # Insertos: la ciudad reacciona (vinetas de los barrios pegadas sobre el mapa, como recortes).
    for x, y, giro, t, img, quien, dice in ((1240, 560, -1.6, 10.1, Crop((620, 240, 1100, 620), "images/bg/barrio_sur.jpg"), "@vecina.ana · Barrio Sur", "¿Es verdad lo del agua? Mis hijos van al colegio en una hora."),
                                            (120, 520, 1.2, 11.9, Crop((300, 120, 1100, 620), "images/bg/barrio_centro.jpg"), "@don.pedro · Centro", "En el súper de la 9 ya no queda agua embotellada.")):
        frame at ap_inserto(t, giro):
            pos (x, y)
            background Solid(AP_PAPEL)
            padding (10, 10, 10, 14)
            vbox:
                spacing 8
                add img size (540, 304)
                vbox:
                    xsize 540
                    text quien size 16 bold True color AP_VINO
                    text dice size 21 color AP_TINTA

    textbutton "Saltar ›" style "arena_link_claro" xalign 0.985 yalign 0.975 action Return()
    key "dismiss" action Return()
    key "civ_accion" action Return()
    timer 15.6 action Return()
    # Sonido sincronizado con la imagen: notificaciones, silencio en el primer plano, tension en el mapa.
    timer 3.2 action Function(sfx, "notificacion")
    timer 4.4 action Function(renpy.sound.play, "assets/audio/sfx/ui_click.wav")
    timer 5.2 action Function(renpy.sound.play, "assets/audio/sfx/ui_click.wav")
    timer 6.3 action Function(renpy.music.stop, fadeout=0.4)
    timer 8.2 action [Function(musica, "tension", 0.6), Function(sfx, "alarma")]
    timer 10.1 action Function(renpy.sound.play, "assets/audio/sfx/notificacion.wav")
    timer 11.9 action Function(renpy.sound.play, "assets/audio/sfx/notificacion.wav")

## ---------------- Escena 4: la decision, dentro del despacho ----------------
## Pantalla del menu real (menu (screen="apertura_decision")): guardado, rollback y QA la respetan.
## Telefono a la izquierda, Claudia a la derecha (sigue en escena), respuestas como acciones del telefono.
screen apertura_decision(items):
    modal True
    default ver_fuente = False
    add Solid(AP_NOCHE) alpha 0.45
    fixed at ap_aparece(0.0, -40, 0):
        pos (120, 90)
        xysize (780, 800)
        add Solid(AP_TINTA)
        frame:
            pos (16, 16)
            xysize (748, 768)
            background Solid(AP_PAPEL)
            padding (34, 26)
            vbox:
                spacing 12
                text "CIVITAS · TENDENCIA EN CIUDAD NOVA" size 16 bold True color AP_VINO kerning 3
                hbox:
                    spacing 14
                    add circulo("#3a3350", AP_RUMOR, 22) yalign 0.5
                    vbox:
                        text "@verdad.oculta" size 24 bold True color AP_TINTA
                        text "hace 58 min · cuenta creada ayer" size 17 color "#8b84a8"
                text "URGENTE: el Acueducto CONFIRMA que el agua de Ciudad Nova está contaminada. No la tomen." size 29 bold True color AP_TINTA
                hbox:
                    spacing 30
                    text "18.900 reposts" size 20 bold True color AP_RUMOR
                    text "40.210 me gusta" size 20 color "#8b84a8"
                if ver_fuente:
                    frame:
                        background Solid("#efe8f5")
                        padding (16, 10)
                        xfill True
                        text "Adjunta una captura sin enlace ni fecha, cortada justo debajo del título." size 20 color AP_TINTA
                else:
                    textbutton "Ver de dónde salió" style "arena_link" action [SetScreenVariable("ver_fuente", True), Function(dar_pista, "captura_veneno")]
                null height 14
                text "RESPONDER COMO ALCALDE" size 16 bold True color AP_VINO kerning 3
                for i, item in enumerate(items):
                    textbutton item.caption style "apertura_opcion" text_style "apertura_opcion_texto" action item.action at ap_aparece(0.25 + i * 0.08) default_focus (i == 0)

style apertura_opcion is default:
    background Solid("#ffffff")
    hover_background Solid("#e9e1f3")
    xfill True
    left_padding 22
    right_padding 22
    top_padding 16
    bottom_padding 16
    hover_sound "assets/audio/sfx/menu_hover.ogg"
    activate_sound "assets/audio/sfx/decision.ogg"
style apertura_opcion_texto is default:
    size 25
    bold True
    color AP_TINTA
    hover_color AP_VINO

## ---------------- Escena 5: la consecuencia (BFS de TU respuesta sobre el mapa) ----------------
screen apertura_reaccion(eleccion, niveles, padres, bloqueados):
    modal True
    default vista = apertura_reaccion_vista(niveles, padres, bloqueados)
    default listo = persistent.reducir_movimiento
    $ resp = APERTURA_RESPUESTA[eleccion]
    add vista
    frame at ap_aparece(0.3, 40, 0):
        xpos 1330 yalign 0.96
        xsize 530
        background Solid(AP_PAPEL)
        padding (34, 28)
        vbox:
            spacing 10
            text resp["titulo"].upper() size 26 bold True color AP_VINO kerning 2
            text resp["texto"] size 20 color AP_TINTA
            null height 4
            hbox:
                spacing 14
                add DynamicDisplayable(vista.texto_alcance)
                text "de %d cuentas\nrecibieron el rumor" % (red_civitas.cantidad_nodos() - 1) size 19 color "#5b4f72" yalign 0.6
            if bloqueados:
                hbox:
                    spacing 10
                    add circulo(AP_FRENO, AP_TINTA, 9) yalign 0.5
                    text "Cuentas que tu respuesta frenó" size 18 color "#5b4f72"
            null height 6
            for k in ("confianza", "desinformacion", "info_verificada"):
                $ antes = apertura_antes.get(k, getattr(ciudad, k))
                $ ahora = getattr(ciudad, k)
                $ bueno = (ahora - antes > 0) != (k in INDICADOR_NEGATIVO)
                vbox:
                    hbox:
                        xfill True
                        text NOMBRES_INDICADOR[k] size 18 color AP_TINTA
                        text (("%+d" % (ahora - antes)) if ahora != antes else "=") size 18 bold True color ("#2f9e8f" if (bueno and ahora != antes) else (AP_RUMOR if ahora != antes else "#8b84a8")) xalign 1.0
                    bar value AnimatedValue(ahora, 100, 1.2, antes) xfill True ysize 10 left_bar Solid("#b9aecb" if ahora == antes else ("#2f9e8f" if bueno else AP_RUMOR)) right_bar Solid("#e6deee")
            null height 6
            frame:
                background Solid("#efe8f5")
                padding (16, 10)
                xfill True
                vbox:
                    text resp["voz"][0] size 16 bold True color AP_VINO
                    text resp["voz"][1] size 20 color AP_TINTA
            if listo:
                textbutton "Continuar" style "apertura_opcion" text_style "apertura_opcion_texto" action Return() default_focus True at ap_aparece(0.0)
    timer 4.2 action SetScreenVariable("listo", True)
    if not listo:
        key "dismiss" action [Function(vista.terminar), SetScreenVariable("listo", True)]
        key "civ_accion" action [Function(vista.terminar), SetScreenVariable("listo", True)]
    else:
        key "civ_accion" action Return()

## ---------------- Escena 6: del telefono de Claudia a la moderacion ----------------
screen apertura_a_moderacion():
    modal True
    add "bg despacho"
    add Solid(AP_NOCHE) alpha 0.5
    fixed at ap_al_telefono:
        xysize (560, 760)
        add Solid(AP_TINTA)
        frame:
            pos (14, 14)
            xysize (532, 732)
            background Solid(AP_PAPEL)
            padding (26, 24)
            vbox:
                spacing 12
                text "COMENTARIOS · 1.204 NUEVOS" size 15 bold True color AP_VINO kerning 3
                for quien, dice, _b in COMENTARIOS_APERTURA:
                    vbox:
                        text quien size 17 bold True color AP_TINTA
                        text dice size 18 color "#5b4f72"
    timer 0.75 action Return()
    timer 0.05 action Function(renpy.sound.play, "assets/audio/sfx/transicion.ogg")

## ---------------- Escena 7: el titulo ----------------
screen apertura_titulo():
    modal True
    add Solid(AP_NOCHE)
    add Transform("images/bg/mapa.jpg", zoom=0.625) at ap_velo(0.0, 1.0, 0.0, 1.0)
    add Solid("#120d1cec")
    add TituloRed()
    vbox at ap_aparece(1.75, 0, 8):
        xalign 0.5 ypos 660
        spacing 18
        text "ALCALDE DIGITAL" style "ap_marca" size 34 kerning 22 color AP_RUMOR xalign 0.5
        text "Cada publicación cambia la ciudad." style "ap_marca" size 28 kerning 2 color AP_LILA xalign 0.5 at ap_aparece(0.6, 0, 6)
    timer 4.8 action Return()
    key "dismiss" action Return()
    key "civ_accion" action Return()
    timer 0.3 action Function(renpy.sound.play, "assets/audio/sfx/transicion.ogg")
    timer 0.35 action Function(musica, "revelacion", 0.8)

## ---------------- Microprueba de Moderacion Express ----------------
## El mismo motor y la misma pantalla del minijuego (ColaModeracion + moderador_ui), con 4 comentarios
## propios y sin tocar registro_minijuegos (el reto completo del lunes puntua aparte).
label apertura_microprueba:
    $ comentarios_ap = [Publicacion(a, t, bot, 0, None) for a, t, bot in COMENTARIOS_APERTURA]
    $ creadas_ap = {"@aguasegura_YA_77": "hace 2 días", "@rosa.del.sur": "2018", "@despierta_nova_x": "ayer", "@hector.taxi": "2016"}
    $ moderacion_ap = ColaModeracion(comentarios_ap, tiempo_por_tarjeta=6.0, cuenta_regresiva=1.5)
    $ ocultar_avisos_juego()
    window hide
    call screen apertura_a_moderacion
    $ apertura_marca("microprueba")
    $ moderacion_intro = "Los comentarios de la publicación están llenos de bots."
    call screen moderador_ui(moderacion_ap, creadas_ap)
    $ moderacion_intro = "Los comentarios de Martina están llenos de bots."
    hide screen moderador_feedback
    $ renpy.block_rollback()
    return apertura_micro_resultado(moderacion_ap)
