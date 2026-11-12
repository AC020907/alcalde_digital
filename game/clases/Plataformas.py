"""
Ruta de la Verdad - Infiltracion NOVA: motor del plataformero 2D (logica pura, sin Ren'Py).

Sustituye al arcade repetido de La Gran Viralizacion: la crisis narrativa sigue, pero la respuesta del
jugador es entrar al sistema de NOVA, esquivar sus defensas y rescatar los fragmentos de evidencia.

Diseno para que sea justo y verificable:
- Paso fijo (60 ticks/s) y SOLO aritmetica entera (subpixeles de 1/16 px): el mismo nivel y las mismas
  entradas dan exactamente el mismo resultado en Python, en Ren'Py a cualquier FPS y en el motor JS del
  navegador (tests/test_plataformas_web.py lo comprueba). Por eso una partida se puede REJUGAR en el
  servidor a partir de la traza de entradas: el cliente nunca envia su puntuacion.
- Salto con coyote time y jump buffering; sin doble salto; salto variable al soltar.
- Colisiones por ejes contra una rejilla de tiles; la velocidad maxima es menor que un tile (sin tuneles).

Entradas por tick: mascara de bits IZQ=1, DER=2, SALTO=4.
"""

TICKS_S = 60
SUB = 16                    # subpixeles por pixel
TILE = 48                   # px
T = TILE * SUB
ANCHO, ALTO = 30 * SUB, 42 * SUB          # caja del jugador
IZQ, DER, SALTO = 1, 2, 4

V_MAX = 76                  # 4.75 px/tick
ACEL_SUELO, ACEL_AIRE, FRENO = 10, 6, 12
GRAVEDAD, V_CAIDA_MAX = 10, 208
V_SALTO, V_CORTE = -196, -70             # ~2.5 tiles de altura; al soltar se recorta
COYOTE, BUFFER = 6, 7                    # ticks
RESPAWN_TICKS = 36
PARPADEO = 80               # ticks encendido / apagado de los bloques intermitentes '~'
MARGEN_PINCHO = 9 * SUB     # la caja de dano de un pincho es mas pequena que el tile (justo para el jugador)
ESQUINA = 7 * SUB           # correccion de esquina: si la cabeza roza el borde de un bloque al saltar, se desliza

SOLIDO, PINCHO, INTERMITENTE = "#", "^", "~"
EVIDENCIA, CONTROL, INICIO, META = "E", "C", "S", "M"

# Fragmentos de evidencia (significado narrativo de cada coleccionable, en orden de aparicion).
FRAGMENTOS = (
    "Registro de creación de @verdad.oculta",
    "Factura de Resonancia S.A.S. por «gestión de conversación»",
    "Lista de 140 cuentas automáticas",
    "Plantilla del rumor del agua con campos por rellenar",
    "Horario de publicación: cada 7 minutos exactos",
    "Captura original del análisis del Acueducto (sin editar)",
    "Orden de pago a la granja de bots",
    "Chat interno: «que parezca que lo dice un vecino»",
)

# Los niveles se arman con tramos de 8 filas (las 3 de arriba van vacias). Asi cada obstaculo se disena y se
# prueba una vez, y los niveles de Historia, Arena y Feria comparten geometria conocida.
# Leyenda: # suelo/pared  ^ pinchos (foso)  ~ bloque intermitente  E evidencia  C punto de control  S inicio  M meta
TRAMOS = {
    "inicio": ["........", "........", "........", "........", "........", ".S....E.", "########", "########"],
    "hueco2": ["........", "........", "........", "........", "........", "........", "###..###", "###..###"],
    "hueco3": [".........", ".........", ".........", ".........", ".........", ".........", "###...###", "###...###"],
    "pinchos2": ["........", "........", "........", "........", "...E....", "........", "###^^###", "########"],
    "pinchos3": [".........", ".........", ".........", ".........", ".........", ".........", "###^^^###", "#########"],
    "escalon": [".........", ".........", ".........", "....E....", "...###...", ".........", "#########", "#########"],
    "torre": ["............", "......E.....", ".....###....", "............", "..##........", "............", "############", "############"],
    "puente": ["..........", "..........", "..........", "..........", "..........", "..........", "###~~~~###", "###....###"],
    "alta": [".....", ".....", ".....", "..E..", ".....", ".....", "#####", "#####"],
    "control": [".....", ".....", ".....", ".....", ".....", "..C..", "#####", "#####"],
    "meta": ["........", "........", "........", "........", "........", "....M...", "########", "########"],
}
RECORRIDOS = {
    "tutorial": (60, "inicio escalon hueco2 control pinchos2 alta meta"),
    "historia": (120, "inicio hueco2 escalon control pinchos2 hueco3 torre control puente alta pinchos3 control "
                      "escalon hueco2 torre control puente pinchos2 hueco3 meta"),
    "arena": (80, "inicio hueco2 escalon control pinchos2 torre control puente alta pinchos3 control hueco3 escalon meta"),
    "feria": (55, "inicio hueco2 escalon control pinchos2 torre control hueco3 alta meta"),
}


def _armar(tramos):
    filas = ["", "", ""] + [""] * 8
    for nombre in tramos.split():
        t = TRAMOS[nombre]
        ancho = len(t[0])
        for k in range(3):
            filas[k] += "." * ancho
        for k in range(8):
            filas[3 + k] += t[k]
    return filas


NIVELES = {clave: {"limite_s": limite, "mapa": _armar(tramos)} for clave, (limite, tramos) in RECORRIDOS.items()}


def _piso(a, b):
    """Division entera hacia menos infinito (igual en Python y en el motor JS)."""
    return a // b


EXTRA_MAX_S = 40


class Nivel(object):
    def __init__(self, clave, extra_s=0):
        datos = NIVELES[clave]
        self.clave = clave
        self.filas = datos["mapa"]
        self.alto = len(self.filas)
        self.ancho = len(self.filas[0])
        if any(len(f) != self.ancho for f in self.filas):
            raise ValueError("nivel %s: filas de distinto ancho" % clave)
        # extra_s: ayuda (o estorbo) narrativo de la Historia; en la Arena siempre es 0 (mismas condiciones).
        self.extra_s = max(-EXTRA_MAX_S, min(EXTRA_MAX_S, int(extra_s)))
        self.limite_ticks = (datos["limite_s"] + self.extra_s) * TICKS_S
        self.evidencias, self.controles = [], []
        self.inicio = self.meta = None
        for fy, fila in enumerate(self.filas):
            for fx, ch in enumerate(fila):
                if ch == EVIDENCIA:
                    self.evidencias.append((fx, fy))
                elif ch == CONTROL:
                    self.controles.append((fx, fy))
                elif ch == INICIO:
                    self.inicio = (fx, fy)
                elif ch == META:
                    self.meta = (fx, fy)
        self.evidencias.sort()
        if self.inicio is None or self.meta is None:
            raise ValueError("nivel %s: falta inicio o meta" % clave)

    def tile(self, fx, fy):
        if fx < 0 or fx >= self.ancho:
            return SOLIDO                      # paredes invisibles en los bordes del mundo
        if fy < 0 or fy >= self.alto:
            return "."
        return self.filas[fy][fx]

    def solido(self, fx, fy, tick):
        ch = self.tile(fx, fy)
        if ch == SOLIDO:
            return True
        return ch == INTERMITENTE and intermitente_activo(tick)


def intermitente_activo(tick):
    return _piso(tick, PARPADEO) % 2 == 0


class Partida(object):
    """Estado de una carrera. avanzar(mascara) simula UN tick."""

    def __init__(self, clave="historia", extra_s=0):
        self.nivel = Nivel(clave, extra_s)
        self.tick = 0
        self.estado = "jugando"            # "meta" | "tiempo" | "abandono"
        self.recogidas = []                # indices de evidencia, en orden
        self.muertes = 0
        self.control = self.nivel.inicio   # ultimo punto de control (tile)
        self.respawn = 0
        self.eventos = []                  # (tick, tipo, dato) para sonido y efectos; no afecta a las reglas
        self.traza = []                    # [[mascara, ticks], ...] (RLE) para rejugar en el servidor
        self.salto_previo = False
        self._colocar(self.nivel.inicio)

    # ----- utilidades -----
    def _colocar(self, tile):
        fx, fy = tile
        self.x = fx * T + _piso(T - ANCHO, 2)
        self.y = (fy + 1) * T - ALTO
        self.vx = self.vy = 0
        self.en_suelo = False
        self.coyote = self.buffer = 0
        self.mira = 1

    def _choca(self, x, y):
        n, t = self.nivel, self.tick
        fx0, fx1 = _piso(x, T), _piso(x + ANCHO - 1, T)
        fy0, fy1 = _piso(y, T), _piso(y + ALTO - 1, T)
        for fy in range(fy0, fy1 + 1):
            for fx in range(fx0, fx1 + 1):
                if n.solido(fx, fy, t):
                    return True
        return False

    def _toca(self, fx, fy, margen=0):
        """La caja del jugador solapa el tile (fx, fy), reducido por margen."""
        return (self.x < (fx + 1) * T - margen and self.x + ANCHO > fx * T + margen and
                self.y < (fy + 1) * T - margen and self.y + ALTO > fy * T + margen)

    def jugando(self):
        return self.estado == "jugando"

    # ----- simulacion -----
    def avanzar(self, mascara):
        if not self.jugando():
            return
        mascara &= 7
        if self.traza and self.traza[-1][0] == mascara:
            self.traza[-1][1] += 1
        else:
            self.traza.append([mascara, 1])
        self.tick += 1
        if self.tick >= self.nivel.limite_ticks:
            self.estado = "tiempo"
            self.eventos.append((self.tick, "tiempo", None))
            return
        if self.respawn > 0:
            self.respawn -= 1
            self.salto_previo = bool(mascara & SALTO)
            return

        # horizontal
        direccion = (1 if mascara & DER else 0) - (1 if mascara & IZQ else 0)
        if direccion:
            self.mira = direccion
            acel = ACEL_SUELO if self.en_suelo else ACEL_AIRE
            self.vx = max(-V_MAX, min(V_MAX, self.vx + direccion * acel))
        elif self.vx > 0:
            self.vx = max(0, self.vx - FRENO)
        elif self.vx < 0:
            self.vx = min(0, self.vx + FRENO)

        # salto: buffer al pulsar, coyote al dejar el suelo, recorte al soltar
        salto = bool(mascara & SALTO)
        if salto and not self.salto_previo:
            self.buffer = BUFFER
        elif self.buffer > 0:
            self.buffer -= 1
        if self.en_suelo:
            self.coyote = COYOTE
        elif self.coyote > 0:
            self.coyote -= 1
        if self.buffer > 0 and self.coyote > 0:
            self.vy = V_SALTO
            self.buffer = self.coyote = 0
            self.en_suelo = False
            self.eventos.append((self.tick, "salto", None))
        if not salto and self.vy < V_CORTE:
            self.vy = V_CORTE
        self.salto_previo = salto
        self.vy = min(V_CAIDA_MAX, self.vy + GRAVEDAD)

        # mover y resolver por ejes
        nx = self.x + self.vx
        if self._choca(nx, self.y):
            if self.vx > 0:
                nx = _piso(nx + ANCHO - 1, T) * T - ANCHO
            elif self.vx < 0:
                nx = (_piso(nx, T) + 1) * T
            else:
                nx = self.x
            if self._choca(nx, self.y):       # un bloque intermitente aparecio encima: no moverse
                nx = self.x
            self.vx = 0
        self.x = nx
        ny = self.y + self.vy
        estaba_en_suelo = self.en_suelo
        self.en_suelo = False
        if self.vy < 0 and self._choca(self.x, ny):
            # Correccion de esquina: un salto que solo roza el borde de un bloque no se corta; se desliza a un lado.
            for dx in range(SUB, ESQUINA + 1, SUB):
                if not self._choca(self.x + dx, ny) and not self._choca(self.x + dx, self.y):
                    self.x += dx
                    break
                if not self._choca(self.x - dx, ny) and not self._choca(self.x - dx, self.y):
                    self.x -= dx
                    break
        if self._choca(self.x, ny):
            if self.vy > 0:
                ny = _piso(ny + ALTO - 1, T) * T - ALTO
                self.en_suelo = True
            elif self.vy < 0:
                ny = (_piso(ny, T) + 1) * T
            else:
                ny = self.y
            if self._choca(self.x, ny):
                ny = self.y
            if self.en_suelo and not estaba_en_suelo:
                self.eventos.append((self.tick, "aterriza", None))
            self.vy = 0
        self.y = ny

        # mundo: caida, pinchos, bloque que se materializa sobre el jugador
        n = self.nivel
        if self.y > n.alto * T or self._choca(self.x, self.y):
            return self._morir()
        fx0, fx1 = _piso(self.x, T), _piso(self.x + ANCHO - 1, T)
        fy0, fy1 = _piso(self.y, T), _piso(self.y + ALTO - 1, T)
        for fy in range(fy0, fy1 + 1):
            for fx in range(fx0, fx1 + 1):
                ch = n.tile(fx, fy)
                if ch == PINCHO and self._toca(fx, fy, MARGEN_PINCHO):
                    return self._morir()
                if ch == EVIDENCIA:
                    i = n.evidencias.index((fx, fy))
                    if i not in self.recogidas:
                        self.recogidas.append(i)
                        self.eventos.append((self.tick, "evidencia", i))
                elif ch == CONTROL and (fx, fy) != self.control and fx > self.control[0]:
                    self.control = (fx, fy)
                    self.eventos.append((self.tick, "control", None))
                elif ch == META:
                    self.estado = "meta"
                    self.eventos.append((self.tick, "meta", None))
                    return

    def _morir(self):
        self.muertes += 1
        self.respawn = RESPAWN_TICKS
        self.eventos.append((self.tick, "dano", None))
        self._colocar(self.control)

    def abandonar(self):
        if self.jugando():
            self.estado = "abandono"

    # ----- resultados -----
    def completado(self):
        return self.estado == "meta"

    def puntuacion(self):
        """0-1000. Dominan las evidencias y llegar a la meta; tiempo y muertes solo ajustan (y solo si se llega)."""
        total = len(self.nivel.evidencias)
        p = _piso(550 * len(self.recogidas) + _piso(total, 2), total) if total else 0
        if self.completado():
            resto = max(0, self.nivel.limite_ticks - self.tick)
            p += 250 + _piso(150 * resto, self.nivel.limite_ticks) + max(0, 50 - 10 * self.muertes)
        return p

    def calificacion(self):
        if not self.completado():
            return "D"
        p = self.puntuacion()
        return "S" if p >= 900 else "A" if p >= 780 else "B" if p >= 640 else "C"

    def resumen(self):
        return {"score_raw": self.puntuacion(), "score_normalized": self.puntuacion(), "completed": self.completado(),
                "evidence": len(self.recogidas), "evidence_total": len(self.nivel.evidencias), "deaths": self.muertes,
                "elapsed_ms": _piso(self.tick * 1000, TICKS_S), "estado": self.estado}

    def resultado(self):
        """Contrato de los minijuegos de la Historia. La clave sigue siendo 'viralizacion': es la respuesta del
        jugador a La Gran Viralizacion, y asi finales, expediente y puntuacion no cambian."""
        nota = self.calificacion()
        if nota in ("S", "A"):
            consecuencia = {"desinformacion": -7, "confianza": 4, "conflictos": -3, "puntos": 14}
        elif nota in ("B", "C"):
            consecuencia = {"desinformacion": -3, "confianza": 2, "puntos": 7}
        else:
            consecuencia = {"desinformacion": 7, "conflictos": 4, "confianza": -4}
        r = self.resumen()
        mensaje = ("Recuperaste %d de %d fragmentos y saliste del sistema de NOVA." % (r["evidence"], r["evidence_total"])
                   if self.completado() else
                   "NOVA cerró la sesión antes de que llegaras al archivo." if self.estado == "tiempo" else
                   "Saliste del sistema sin el archivo.")
        return {"minijuego": "viralizacion", "exito": self.completado(), "calificacion": nota, "puntos": r["score_raw"],
                "evidencias": r["evidence"], "evidencias_total": r["evidence_total"], "muertes": self.muertes,
                "segundos": r["elapsed_ms"] / 1000.0, "mensaje": mensaje, "consecuencia": consecuencia}


class TrazaInvalida(ValueError):
    pass


def rejugar(clave, traza, extra_s=0, max_segmentos=6000):
    """Reproduce una traza [[mascara, ticks], ...] y devuelve la Partida resultante (el servidor puntua con esto)."""
    if clave not in NIVELES:
        raise TrazaInvalida("Nivel desconocido.")
    if not isinstance(traza, list) or len(traza) > max_segmentos:
        raise TrazaInvalida("Traza inválida.")
    p = Partida(clave, extra_s)
    limite = p.nivel.limite_ticks
    total = 0
    for seg in traza:
        if (not isinstance(seg, (list, tuple)) or len(seg) != 2 or any(isinstance(v, bool) or not isinstance(v, int) for v in seg)
                or not 0 <= seg[0] <= 7 or not 1 <= seg[1] <= limite):
            raise TrazaInvalida("Segmento de traza inválido.")
        total += seg[1]
        if total > limite:
            raise TrazaInvalida("La traza dura más que el nivel.")
        for _ in range(seg[1]):
            p.avanzar(seg[0])
            if not p.jugando():
                return p
    p.abandonar()      # la traza termino antes que la carrera: cuenta lo conseguido hasta ahi
    return p


class Piloto(object):
    """Jugador automatico (pruebas, QA visual y bots de la Arena): corre a la derecha y salta al borde de huecos,
    fosos y escalones. Con poca habilidad se precipita o reacciona tarde, y no busca las evidencias altas."""

    def __init__(self, rng, habilidad=1.0):
        self.rng, self.habilidad, self.mantener = rng, habilidad, 0

    def mascara(self, p):
        n, rng = p.nivel, self.rng
        frente = p.x + ANCHO - 1
        ft = _piso(frente, T)
        fy = _piso(p.y + ALTO - 1, T)
        falta = (ft + 1) * T - frente
        mascara = DER
        if self.mantener > 0:
            self.mantener -= 1
            mascara |= SALTO
        elif p.en_suelo and p.respawn == 0:
            abajo, delante = n.tile(ft + 1, fy + 1), n.tile(ft + 1, fy)
            foso = abajo in (".", PINCHO, EVIDENCIA, CONTROL) or (abajo == INTERMITENTE and not intermitente_activo(p.tick + 40))
            margen = 12 * SUB + (0 if rng.random() < self.habilidad else rng.randint(-40, 40) * SUB)
            arriba = any(n.tile(ft + k, fy - 2) == EVIDENCIA or n.tile(ft + k, fy - 1) == SOLIDO for k in (1, 2))
            if (foso and falta <= margen) or delante == SOLIDO or (arriba and rng.random() < self.habilidad * 0.5):
                mascara |= SALTO
                self.mantener = 22
        return mascara


def bot(clave, rng, habilidad=1.0):
    p = Partida(clave)
    piloto = Piloto(rng, habilidad)
    while p.jugando():
        p.avanzar(piloto.mascara(p))
    return p


def config_cliente(clave, extra_s=0):
    """Todo lo que necesita el motor del navegador (plat_motor.js): constantes y mapa salen de este modulo."""
    n = Nivel(clave, extra_s)
    return {"nivel": clave, "filas": list(n.filas), "limite_ticks": n.limite_ticks, "ticks_s": TICKS_S, "sub": SUB, "tile": TILE,
            "fragmentos": list(FRAGMENTOS),
            "constantes": {"T": T, "ANCHO": ANCHO, "ALTO": ALTO, "V_MAX": V_MAX, "ACEL_SUELO": ACEL_SUELO, "ACEL_AIRE": ACEL_AIRE,
                           "FRENO": FRENO, "GRAVEDAD": GRAVEDAD, "V_CAIDA_MAX": V_CAIDA_MAX, "V_SALTO": V_SALTO, "V_CORTE": V_CORTE,
                           "COYOTE": COYOTE, "BUFFER": BUFFER, "RESPAWN_TICKS": RESPAWN_TICKS, "PARPADEO": PARPADEO,
                           "MARGEN_PINCHO": MARGEN_PINCHO, "ESQUINA": ESQUINA}}
