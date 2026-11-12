"""
Caza-Rumores para la Arena Online: el unico reto de punteria. El rumor salta de cuenta en cuenta por el grafo
social de Ciudad Nova (las mismas cuentas y seguimientos de reglas.py) y el jugador lo intercepta tocando cada
"paquete" mientras viaja por una conexion.

Motor a paso fijo (50 ms) y solo enteros, igual en Python y en el navegador (caza_motor.js; paridad en
tests/test_caza_web.py). El cliente envia la lista de intercepciones [tick, paquete, x, y]; el servidor REJUEGA
la propagacion completa y comprueba que cada toque cayo sobre un paquete que estaba en vuelo y cerca del dedo.

Propagacion (BFS por oleadas, con tiempos):
- las cuentas foco empiezan contagiadas; una cuenta contagiada envia el rumor a cada seguidor sano;
- si el paquete llega sin ser interceptado, el seguidor se contagia y empieza a reenviar;
- una cuenta contagiada reintenta cada cierto tiempo con sus seguidores sanos: hay que sostener la contencion.
"""
import random

from clases.arena.reglas import CIUDADANOS, SEGUIMIENTOS, ZONAS

TICK_MS = 50
ANCHO, ALTO = 1000, 700                      # espacio virtual del mapa (el navegador lo escala)
CENTRO_ZONA = {"colegio": (500, 110), "barrio": (500, 300), "parque": (220, 480), "plaza": (760, 440), "alcaldia": (880, 625)}
# Desplazamientos fijos alrededor del centro de cada zona (enteros: sin trigonometria que pueda diferir).
ANILLO = ((0, -50), (70, -8), (44, 46), (-44, 46), (-70, -8))
RADIO_TOQUE = 46
TOLERANCIA_TOQUE = 60                         # holgura del servidor: un tick de movimiento + dedo
MAX_TOQUES = 400
MODOS = {
    "completo": {"duracion_ms": 34000, "focos": 2, "retardo_ms": 900, "escalon_ms": 350, "reemision_ms": 2600, "viaje_ms": 2300},
    "feria": {"duracion_ms": 24000, "focos": 2, "retardo_ms": 800, "escalon_ms": 300, "reemision_ms": 2400, "viaje_ms": 2100},
}


class ToquesInvalidos(ValueError):
    pass


def config(modo, semilla):
    """Escenario identico para todos los jugadores de la sala: cuentas, posiciones, conexiones, focos y tiempos."""
    m = MODOS[modo]
    por_zona = {}
    nodos = []
    for nid, nombre, zona in CIUDADANOS:
        k = por_zona.get(zona, 0)
        por_zona[zona] = k + 1
        cx, cy = CENTRO_ZONA[zona]
        dx, dy = ANILLO[k % len(ANILLO)]
        nodos.append({"id": nid, "nombre": nombre, "zona": zona, "x": cx + dx, "y": cy + dy})
    ids = [n["id"] for n in nodos]
    aristas = []
    for a, b, peso in SEGUIMIENTOS:
        if a in ids and b in ids:
            # Un seguimiento fuerte transmite antes (peso 0.5-0.8 -> viaje mas corto).
            aristas.append([a, b, m["viaje_ms"] + (70 - int(round(peso * 100))) * 12])
    rng = random.Random("caza|%s" % semilla)
    con_salida = sorted({a for a, _, _ in aristas})
    focos = rng.sample(con_salida, m["focos"])
    return {"modo": modo, "semilla": semilla, "tick_ms": TICK_MS, "ancho": ANCHO, "alto": ALTO, "zonas": list(ZONAS),
            "centros": {z: list(c) for z, c in CENTRO_ZONA.items()}, "nodos": nodos, "aristas": aristas, "focos": focos,
            "duracion_ms": m["duracion_ms"], "retardo_ms": m["retardo_ms"], "escalon_ms": m["escalon_ms"],
            "reemision_ms": m["reemision_ms"], "radio_toque": RADIO_TOQUE}


class Caza(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.pos = {n["id"]: (n["x"], n["y"]) for n in cfg["nodos"]}
        self.salidas = {}
        for a, b, dur in cfg["aristas"]:
            self.salidas.setdefault(a, []).append((b, dur))
        self.tick = 0
        self.total_ticks = cfg["duracion_ms"] // TICK_MS
        self.contagiados = {}             # nodo -> ms en que se contagio (orden de insercion = orden de contagio)
        self.orden = []
        self.proximo = {}                 # "a>b" -> ms del siguiente envio
        self.paquetes = []                # {id, a, b, sale, llega, estado: vuelo | interceptado | llego}
        self.interceptados = 0
        self.eventos = []
        for f in cfg["focos"]:
            self._contagiar(f, 0)

    def _contagiar(self, nodo, t):
        if nodo in self.contagiados:
            return
        self.contagiados[nodo] = t
        self.orden.append(nodo)
        self.eventos.append((t, "contagio", nodo))
        for k, (b, _dur) in enumerate(self.salidas.get(nodo, ())):
            self.proximo[nodo + ">" + b] = t + self.cfg["retardo_ms"] + k * self.cfg["escalon_ms"]

    def terminado(self):
        return self.tick >= self.total_ticks

    def en_vuelo(self, pid):
        return 0 <= pid < len(self.paquetes) and self.paquetes[pid]["estado"] == "vuelo"

    def posicion(self, pid, t):
        """Posicion entera del paquete en el ms t (interpolacion lineal sobre su conexion)."""
        p = self.paquetes[pid]
        ax, ay = self.pos[p["a"]]
        bx, by = self.pos[p["b"]]
        dur = p["llega"] - p["sale"]
        k = max(0, min(dur, t - p["sale"]))
        return ax + (bx - ax) * k // dur, ay + (by - ay) * k // dur

    def interceptar(self, pid):
        if not self.en_vuelo(pid):
            return False
        self.paquetes[pid]["estado"] = "interceptado"
        self.interceptados += 1
        self.eventos.append((self.tick * TICK_MS, "intercepcion", pid))
        return True

    def avanzar(self):
        if self.terminado():
            return
        self.tick += 1
        t = self.tick * TICK_MS
        for p in self.paquetes:                              # llegadas, en orden de id
            if p["estado"] == "vuelo" and p["llega"] <= t:
                p["estado"] = "llego"
                self._contagiar(p["b"], t)
        activos = {p["a"] + ">" + p["b"] for p in self.paquetes if p["estado"] == "vuelo"}
        for a in list(self.orden):                           # envios, en orden de contagio y de conexion
            for b, dur in self.salidas.get(a, ()):
                clave = a + ">" + b
                if b in self.contagiados or clave in activos or self.proximo[clave] > t:
                    continue
                self.paquetes.append({"id": len(self.paquetes), "a": a, "b": b, "sale": t, "llega": t + dur, "estado": "vuelo"})
                self.proximo[clave] = t + dur + self.cfg["reemision_ms"]
                activos.add(clave)

    def huella(self):
        return [self.tick, len(self.contagiados), len(self.paquetes), self.interceptados,
                sum(1 for p in self.paquetes if p["estado"] == "vuelo")]


def sin_jugador(cfg):
    """Cuantas cuentas se contagian si nadie intercepta nada (referencia para medir la contencion)."""
    c = Caza(cfg)
    while not c.terminado():
        c.avanzar()
    return len(c.contagiados)


def rejugar(cfg, toques):
    """toques: [[tick, paquete, x, y], ...] en orden. Devuelve (Caza, validos)."""
    if not isinstance(toques, list) or len(toques) > MAX_TOQUES:
        raise ToquesInvalidos("Lista de intercepciones inválida.")
    c = Caza(cfg)
    previo = 0
    por_tick = {}
    for tq in toques:
        if (not isinstance(tq, (list, tuple)) or len(tq) != 4 or any(isinstance(v, bool) or not isinstance(v, int) for v in tq)
                or not 1 <= tq[0] <= c.total_ticks or tq[0] < previo):
            raise ToquesInvalidos("Intercepción con formato inválido.")
        previo = tq[0]
        por_tick.setdefault(tq[0], []).append(tq)
    validos = 0
    while not c.terminado():
        for _tick, pid, x, y in por_tick.get(c.tick + 1, ()):     # el toque se aplica antes de simular su tick
            if not c.en_vuelo(pid):
                raise ToquesInvalidos("Se interceptó un rumor que no estaba en vuelo.")
            px, py = c.posicion(pid, c.tick * TICK_MS)
            if (px - x) ** 2 + (py - y) ** 2 > (RADIO_TOQUE + TOLERANCIA_TOQUE) ** 2:
                raise ToquesInvalidos("El toque no cayó sobre el rumor.")
            c.interceptar(pid)
            validos += 1
        c.avanzar()
    return c, validos


def puntuar(cfg, datos):
    """0-1000: domina la contencion (cuentas salvadas); la punteria ajusta. Los fallos los declara el cliente."""
    if not isinstance(datos, dict):
        raise ToquesInvalidos("Resultado inválido.")
    c, validos = rejugar(cfg, datos.get("toques"))
    fallos = datos.get("fallos", 0)
    if isinstance(fallos, bool) or not isinstance(fallos, int) or not 0 <= fallos <= 2000:
        raise ToquesInvalidos("Fallos fuera de rango.")
    base, focos, final = sin_jugador(cfg), len(cfg["focos"]), len(c.contagiados)
    contencion = (base - final) / float(base - focos) if base > focos else 1.0
    punteria = validos / float(validos + fallos) if validos else 0.0
    normalizado = int(round(800 * contencion + 200 * punteria * min(1.0, validos / 6.0)))
    return {"normalizado": max(0, min(1000, normalizado)), "precision": round(contencion, 3),
            "detalle": {"contagiadas": final, "sin_jugador": base, "total": len(cfg["nodos"]), "interceptados": validos,
                        "fallos": fallos, "contenido": contencion >= 0.5},
            "resumen": "%d de %d cuentas a salvo · %d rumores interceptados · puntería %d%%" % (
                len(cfg["nodos"]) - final, len(cfg["nodos"]), validos, int(punteria * 100))}


def toques_bot(cfg, nivel, rng):
    """Jugador automatico: intercepta cada rumor con probabilidad `nivel`, tras un tiempo de reaccion."""
    c = Caza(cfg)
    toques, plan = [], {}
    while not c.terminado():
        for p in c.paquetes:
            if p["id"] not in plan:
                reaccion = rng.randint(8, 24) + int((1 - nivel) * 14)
                plan[p["id"]] = c.tick + reaccion if rng.random() < nivel else None
        for pid, cuando in sorted(plan.items()):
            if cuando is not None and cuando <= c.tick + 1 and c.en_vuelo(pid) and len(toques) < MAX_TOQUES:
                x, y = c.posicion(pid, c.tick * TICK_MS)
                toques.append([c.tick + 1, pid, x + rng.randint(-12, 12), y + rng.randint(-12, 12)])
                c.interceptar(pid)
                plan[pid] = None
        c.avanzar()
    return {"toques": toques, "fallos": int(len(toques) * (1 - nivel) * 0.6)}
