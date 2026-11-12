"""
Motor del Duelo de Frecuencias (minijuego ritmico original). Logica pura, sin Ren'Py.

- Chart declarativo validado: {song_id, version, bpm, offset_ms, difficulty, duration_ms, notes:[{time_ms, lane, type}]}.
- El tiempo de cancion sale de la posicion REAL del audio (RelojCancion); los frames solo dibujan.
- Juez con ventanas configurables: Perfect / Good / Bad / Miss, combo, precision y nota final.
- Maquina de estados: countdown -> playing <-> paused -> results (o aborted).
"""

CARRILES = 4
TIPOS = ("tap",)
SEPARACION_MIN_MS = 90          # dos notas del mismo carril mas juntas son injugables
VENTANAS_MS = {"perfect": 45, "good": 90, "bad": 135}
VALOR_JUICIO = {"perfect": 1.0, "good": 0.7, "bad": 0.3, "miss": 0.0}
UMBRAL_EXITO = 0.6              # precision necesaria para ganar el duelo
NOTAS = ((0.95, "S"), (0.85, "A"), (0.72, "B"), (0.6, "C"))

COUNTDOWN, PLAYING, PAUSED, RESULTS, ABORTED = "countdown", "playing", "paused", "results", "aborted"


def validar_chart(chart):
    """Lista de errores (vacia si el chart es valido)."""
    errores = []
    for clave in ("song_id", "version", "bpm", "offset_ms", "difficulty", "duration_ms", "notes"):
        if clave not in chart:
            errores.append("falta %s" % clave)
    if errores:
        return errores
    if not chart["bpm"] or chart["bpm"] <= 0:
        errores.append("bpm invalido")
    if chart["duration_ms"] <= 0:
        errores.append("duracion invalida")
    notas = chart["notes"]
    if not notas:
        errores.append("chart sin notas")
    ultima_por_carril = {}
    previo = -1
    for i, n in enumerate(notas):
        t, lane, tipo = n.get("time_ms"), n.get("lane"), n.get("type", "tap")
        if not isinstance(t, (int, float)) or t < 0 or t > chart["duration_ms"]:
            errores.append("nota %d: tiempo fuera de rango" % i)
            continue
        if lane not in range(CARRILES):
            errores.append("nota %d: carril invalido" % i)
            continue
        if tipo not in TIPOS:
            errores.append("nota %d: tipo %s no soportado" % (i, tipo))
        if t < previo:
            errores.append("nota %d: fuera de orden" % i)
        previo = t
        anterior = ultima_por_carril.get(lane)
        if anterior is not None and t - anterior < SEPARACION_MIN_MS:
            errores.append("nota %d: demasiado cerca de la anterior en el carril %d" % (i, lane))
        ultima_por_carril[lane] = t
    return errores


class RelojCancion(object):
    """
    Tiempo de cancion en ms a partir de la posicion reproducida del audio.
    Si el motor devuelve None (audio aun no arrancado, web suspendida, mute en algunos backends),
    se extrapola desde la ultima posicion real con el reloj de pared, y se resincroniza en cuanto
    vuelve una posicion valida. Nunca retrocede mas de lo tolerado (evita juicios repetidos).
    """
    TOLERANCIA_RETROCESO_MS = 40
    ESPERA_AUDIO_MS = 1500

    def __init__(self, offset_ms=0.0):
        self.offset_ms = offset_ms     # calibracion del jugador: positivo = audio llega tarde
        self.ultima_pos = None         # (pos_audio_ms, pared_ms)
        self.tiempo = 0.0
        self.desvios = []              # |extrapolado - real| al resincronizar, para medir drift
        self.pausado = False
        self.ultimo_valor = None
        self.inicio_pared = None

    def actualizar(self, pos_audio_s, pared_s):
        pared_ms = pared_s * 1000.0
        if self.pausado:
            return self.tiempo
        # El motor de audio informa la posicion por bloques (~20-45 ms): si el valor no cambio desde
        # la ultima lectura, se extrapola con el reloj de pared en vez de "congelar" la cancion.
        if pos_audio_s is not None and pos_audio_s == self.ultimo_valor:
            pos_audio_s = None
        elif pos_audio_s is not None:
            self.ultimo_valor = pos_audio_s
        if pos_audio_s is not None:
            real = pos_audio_s * 1000.0
            if self.ultima_pos is not None:
                estimado = self.ultima_pos[0] + (pared_ms - self.ultima_pos[1])
                self.desvios.append(abs(estimado - real))
            self.ultima_pos = (real, pared_ms)
            nuevo = real - self.offset_ms
        elif self.ultima_pos is not None:
            nuevo = self.ultima_pos[0] + (pared_ms - self.ultima_pos[1]) - self.offset_ms
        elif self.inicio_pared is not None and pared_ms - self.inicio_pared > self.ESPERA_AUDIO_MS:
            # Navegadores donde el audio nunca informa su posicion: se juega con el reloj de pared.
            nuevo = pared_ms - self.inicio_pared - self.offset_ms
        else:
            if self.inicio_pared is None:
                self.inicio_pared = pared_ms
            return self.tiempo
        if nuevo >= self.tiempo - self.TOLERANCIA_RETROCESO_MS:
            self.tiempo = max(self.tiempo, nuevo)
        return self.tiempo

    def pausar(self):
        self.pausado = True

    def reanudar(self):
        # La pared siguio corriendo durante la pausa: se descarta la referencia para no saltar adelante.
        self.pausado = False
        self.ultima_pos = None
        self.ultimo_valor = None

    def drift_max(self):
        return max(self.desvios) if self.desvios else 0.0


class Duelo(object):
    def __init__(self, chart, ventanas=None, umbral=UMBRAL_EXITO):
        errores = validar_chart(chart)
        if errores:
            raise ValueError("chart invalido: " + "; ".join(errores[:3]))
        self.chart = chart
        self.v = dict(VENTANAS_MS, **(ventanas or {}))
        self.umbral = umbral
        self.notas = [dict(n, estado=None) for n in chart["notes"]]
        self.siguiente_pendiente = 0
        self.conteo = {"perfect": 0, "good": 0, "bad": 0, "miss": 0}
        self.combo = self.max_combo = 0
        self.estado = COUNTDOWN
        self.ultimos = []              # (tiempo, carril, juicio) para efectos visuales

    # ----- ciclo -----
    def empezar(self):
        if self.estado == COUNTDOWN:
            self.estado = PLAYING

    def pausar(self):
        if self.estado == PLAYING:
            self.estado = PAUSED

    def reanudar(self):
        if self.estado == PAUSED:
            self.estado = PLAYING

    def abortar(self):
        if self.estado in (COUNTDOWN, PLAYING, PAUSED):
            self.estado = ABORTED

    def actualizar(self, t_ms):
        """Marca como Miss las notas que ya pasaron su ventana. Termina al acabar la cancion."""
        if self.estado != PLAYING:
            return
        limite = t_ms - self.v["bad"]
        i = self.siguiente_pendiente
        while i < len(self.notas) and self.notas[i]["time_ms"] < limite:
            if self.notas[i]["estado"] is None:
                self._juzgar(i, "miss", t_ms)
            i += 1
        self.siguiente_pendiente = i
        if t_ms >= self.chart["duration_ms"] and all(n["estado"] for n in self.notas):
            self.estado = RESULTS

    def pulsar(self, carril, t_ms):
        """Una pulsacion juzga como mucho UNA nota (la mas antigua pendiente dentro de la ventana).
        Pulsar sin nota no da ni quita puntos: el ruido no se premia y el nerviosismo no se castiga."""
        if self.estado != PLAYING:
            return None
        mejor = None
        for i in range(self.siguiente_pendiente, len(self.notas)):
            n = self.notas[i]
            if n["time_ms"] - t_ms > self.v["bad"]:
                break
            if n["estado"] is None and n["lane"] == carril and abs(n["time_ms"] - t_ms) <= self.v["bad"]:
                mejor = i
                break
        if mejor is None:
            return None
        d = abs(self.notas[mejor]["time_ms"] - t_ms)
        juicio = "perfect" if d <= self.v["perfect"] else "good" if d <= self.v["good"] else "bad"
        self._juzgar(mejor, juicio, t_ms)
        return juicio

    def _juzgar(self, i, juicio, t_ms):
        self.notas[i]["estado"] = juicio
        self.conteo[juicio] += 1
        if juicio in ("perfect", "good"):
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
        else:
            self.combo = 0
        self.ultimos = (self.ultimos + [(t_ms, self.notas[i]["lane"], juicio)])[-8:]

    # ----- resultados -----
    def juzgadas(self):
        return sum(self.conteo.values())

    def precision(self):
        total = len(self.notas)
        if not total:
            return 0.0
        return sum(VALOR_JUICIO[j] * c for j, c in self.conteo.items()) / total

    def calificacion(self):
        p = self.precision()
        for minimo, nota in NOTAS:
            if p >= minimo:
                return nota
        return "D"

    def exito(self):
        return self.estado == RESULTS and self.precision() >= self.umbral

    def visibles(self, t_ms, antes_ms, despues_ms=150):
        """Notas pendientes que caben en pantalla: el dibujo solo recorre esta ventana."""
        res = []
        for i in range(self.siguiente_pendiente, len(self.notas)):
            n = self.notas[i]
            if n["time_ms"] > t_ms + antes_ms:
                break
            if n["estado"] is None and n["time_ms"] >= t_ms - despues_ms:
                res.append(n)
        return res

    def resultado(self):
        nota = self.calificacion()
        exito = self.exito()
        if exito and nota in ("S", "A"):
            consecuencia = {"desinformacion": -5, "confianza": 4, "info_verificada": 3, "puntos": 12}
        elif exito:
            consecuencia = {"desinformacion": -3, "confianza": 2, "puntos": 6}
        else:
            consecuencia = {"desinformacion": 2, "confianza": -1}
        return {
            "minijuego": "ritmo",
            "exito": exito,
            "calificacion": nota,
            "precision": round(self.precision(), 3),
            "max_combo": self.max_combo,
            "conteo": dict(self.conteo),
            "abandonado": self.estado == ABORTED,
            "consecuencia": consecuencia,
        }
