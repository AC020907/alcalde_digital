import math

## Mapa de Ciudad Nova: grafo de calles por donde se maneja el carro.
## Las coordenadas estan en el espacio de referencia del mapa (2000 px de ancho,
## 1333 de alto); la pantalla las escala al dibujar.

ANCHO_REF = 2000
ALTO_REF = 1333

# Orden de los 8 rumbos por sector de 45 grados (0 = derecha, sentido horario en pantalla).
RUMBOS = ("der", "abajo_diag_der", "abajo", "abajo_diag_izq",
          "izq", "arriba_diag_izq", "arriba", "arriba_diag_der")

UBICACIONES_FERIA = ("centro", "barrio_sur", "alcaldia", "prensa")


def rumbo_de_angulo(angulo, previo=None, histeresis=12.0):
    """Sector de 45 grados del angulo (grados, 0 = derecha, positivo hacia abajo).
    Con 'previo' se exige pasar 'histeresis' grados del borde antes de cambiar de rumbo."""
    angulo %= 360.0
    sector = int(((angulo + 22.5) % 360.0) // 45)
    if previo in RUMBOS and RUMBOS[sector] != previo:
        centro = RUMBOS.index(previo) * 45.0
        dif = abs((angulo - centro + 180.0) % 360.0 - 180.0)
        if dif < 22.5 + histeresis:
            return previo
    return RUMBOS[sector]


class MapaCiudad:
    """Grafo no dirigido de calles: nodos con posicion y aristas con su longitud."""

    def __init__(self):
        self.pos = {}        # nodo -> (x, y)
        self.vecinos = {}    # nodo -> set de nodos
        self.paradas = {}    # id de ubicacion -> nodo

    # ===== CONSTRUCCION =====

    def agregar_nodo(self, nodo, x, y, parada=None):
        self.pos[nodo] = (float(x), float(y))
        self.vecinos.setdefault(nodo, set())
        if parada:
            self.paradas[parada] = nodo

    def conectar(self, *nodos):
        """Une los nodos en cadena: conectar('a', 'b', 'c') crea a-b y b-c."""
        for a, b in zip(nodos, nodos[1:]):
            if a == b:
                continue
            self.vecinos[a].add(b)
            self.vecinos[b].add(a)

    # ===== CONSULTAS =====

    def aristas(self):
        vistas = []
        for a, vs in self.vecinos.items():
            for b in vs:
                if a < b:
                    vistas.append((a, b))
        return vistas

    def longitud(self, a, b):
        (xa, ya), (xb, yb) = self.pos[a], self.pos[b]
        return math.hypot(xb - xa, yb - ya)

    def angulo(self, a, b):
        (xa, ya), (xb, yb) = self.pos[a], self.pos[b]
        return math.degrees(math.atan2(yb - ya, xb - xa))

    def es_conexo(self):
        if not self.pos:
            return True
        inicio = next(iter(self.pos))
        vistos, pendientes = {inicio}, [inicio]
        while pendientes:
            actual = pendientes.pop()
            for v in self.vecinos[actual]:
                if v not in vistos:
                    vistos.add(v)
                    pendientes.append(v)
        return len(vistos) == len(self.pos)

    def ubicacion_de_nodo(self, nodo):
        for ubicacion, n in self.paradas.items():
            if n == nodo:
                return ubicacion
        return None


class Carro:
    """Carro sobre el grafo: o esta en un nodo (origen == destino) o en una arista origen -> destino
    con 'avance' pixeles recorridos desde el origen.

    avanzar(dt, dx, dy) recibe la direccion pedida (-1, 0 o 1 en cada eje). En medio de una calle
    solo se puede ir hacia adelante o hacia atras; en un nodo se toma la calle que mejor encaje
    con la direccion pedida (dentro de TOLERANCIA grados) y si ninguna encaja el carro se queda."""

    VELOCIDAD = 330.0      # px de referencia por segundo
    ACELERACION = 900.0
    TOLERANCIA = 67.5

    def __init__(self, mapa, nodo_inicial):
        self.mapa = mapa
        self.origen = nodo_inicial
        self.destino = nodo_inicial
        self.avance = 0.0
        self.velocidad = 0.0
        self.sentido = 1
        self.rumbo = "der"

    # ===== GUARDADO =====

    def estado(self):
        return {"origen": self.origen, "destino": self.destino, "avance": self.avance}

    def restaurar(self, estado):
        """Vuelve a una posicion guardada; si el mapa cambio y ya no es valida, deja el carro en el origen."""
        origen, destino = estado.get("origen"), estado.get("destino")
        if origen in self.mapa.pos and (destino == origen or destino in self.mapa.vecinos.get(origen, ())):
            self.origen, self.destino = origen, destino
            self.avance = max(0.0, min(float(estado.get("avance", 0.0)), self.mapa.longitud(origen, destino)))
            self.velocidad = 0.0

    # ===== POSICION =====

    def en_nodo(self):
        return self.origen == self.destino

    def posicion(self):
        (xa, ya), (xb, yb) = self.mapa.pos[self.origen], self.mapa.pos[self.destino]
        largo = self.mapa.longitud(self.origen, self.destino)
        t = self.avance / largo if largo > 0 else 0.0
        return xa + (xb - xa) * t, ya + (yb - ya) * t

    def ubicacion_cercana(self, radio=70.0):
        x, y = self.posicion()
        mejor, distancia = None, radio
        for ubicacion, nodo in self.mapa.paradas.items():
            px, py = self.mapa.pos[nodo]
            d = math.hypot(px - x, py - y)
            if d <= distancia:
                mejor, distancia = ubicacion, d
        return mejor

    # ===== MOVIMIENTO =====

    def _diferencia(self, a, b):
        return abs((a - b + 180.0) % 360.0 - 180.0)

    def _llegar(self, nodo):
        self.origen = self.destino = nodo
        self.avance = 0.0

    def _calle_hacia(self, nodo, angulo):
        mejor, menor = None, self.TOLERANCIA
        for v in sorted(self.mapa.vecinos[nodo]):
            dif = self._diferencia(self.mapa.angulo(nodo, v), angulo)
            if dif <= menor:
                mejor, menor = v, dif
        return mejor

    def _actualizar_rumbo(self):
        if self.en_nodo():
            return
        angulo = self.mapa.angulo(self.origen, self.destino)
        self.rumbo = rumbo_de_angulo(angulo if self.sentido > 0 else angulo + 180.0, self.rumbo)

    def avanzar(self, dt, dx, dy):
        pidiendo = dx != 0 or dy != 0
        angulo = math.degrees(math.atan2(dy, dx)) if pidiendo else None
        if pidiendo:
            self.velocidad = min(self.VELOCIDAD, self.velocidad + self.ACELERACION * dt)
        else:
            self.velocidad = max(0.0, self.velocidad - self.ACELERACION * dt)
        restante = self.velocidad * dt
        for _ in range(12):
            if restante <= 1e-6:
                break
            if self.en_nodo():
                if not pidiendo:
                    break
                siguiente = self._calle_hacia(self.origen, angulo)
                if siguiente is None:
                    self.velocidad = 0.0
                    break
                self.destino, self.avance, self.sentido = siguiente, 0.0, 1
            elif pidiendo:
                dif = self._diferencia(self.mapa.angulo(self.origen, self.destino), angulo)
                if dif <= self.TOLERANCIA:
                    self.sentido = 1
                elif dif >= 180.0 - self.TOLERANCIA:
                    self.sentido = -1
            largo = self.mapa.longitud(self.origen, self.destino)
            if self.sentido > 0:
                paso = min(restante, largo - self.avance)
                self.avance += paso
                llego = self.avance >= largo - 1e-6
            else:
                paso = min(restante, self.avance)
                self.avance -= paso
                llego = self.avance <= 1e-6
            restante -= paso
            self._actualizar_rumbo()
            if llego:
                self._llegar(self.destino if self.sentido > 0 else self.origen)
                if not pidiendo:
                    self.velocidad = 0.0
                    break


def crear_mapa_nova():
    """Calles de Ciudad Nova sobre images/bg/mapa.jpg (coordenadas de referencia 2000x1333)."""
    m = MapaCiudad()
    nodos = {
        # glorieta de la plaza
        "rot_n": (950, 545), "rot_o": (870, 620), "rot_s": (960, 672), "rot_e": (1050, 618),
        # calle norte de la plaza hacia el Centro y la avenida de Prensa
        "n1": (960, 500), "centro": (972, 455, "centro"), "b1": (1003, 485), "b3": (1038, 525), "b2": (1068, 565),
        "pa": (1180, 585), "pb": (1250, 540), "prensa": (1290, 502, "prensa"), "c4": (1383, 525), "nw_e": (1457, 537),
        "c5": (1520, 590), "c6": (1570, 650), "cruce_e": (1620, 722),
        # calle de la glorieta hacia el este (norte de la Alcaldia)
        "r1": (1110, 592), "r2": (1217, 597), "r3": (1323, 577), "r4": (1417, 568),
        # calle oeste y avenida diagonal
        "w1": (790, 640), "w2": (720, 628), "w3": (650, 618), "w4": (580, 613), "d0": (503, 650),
        "oeste": (350, 630),
        "d1": (630, 717), "parque": (703, 757, "parque"), "d3": (830, 830), "d4": (930, 880),
        "d5": (1000, 930, "barrio_sur"),
        # anillo oeste de la Alcaldia
        "l1": (910, 705), "l2": (903, 760), "l3": (903, 817),
        # calle sur de la Alcaldia
        "s1": (1087, 948), "alcaldia": (1150, 953, "alcaldia"), "s2": (1227, 945), "s3": (1273, 945),
        "s4": (1327, 923), "s5": (1400, 883), "s6": (1453, 850), "s7": (1500, 803), "s8": (1560, 765),
        # camino hacia el Transporte Publico y el sur
        "se1": (1290, 1035, "transporte"), "se2": (1353, 1110), "se3": (1427, 1197), "se4": (1453, 1243),
        # camino de Barrio Norte y la Universidad
        "bn1": (535, 590), "barrio_norte": (617, 512, "barrio_norte"), "bn2": (640, 470), "bn3": (650, 417),
        "j": (670, 350, "universidad"), "nw1": (630, 323), "nw2": (550, 283), "nw3": (483, 237),
        "nw4": (403, 177),
        "u1": (800, 345), "u2": (900, 322), "u3": (1000, 305), "u4": (1050, 285), "u5": (1150, 225),
        "u6": (1203, 197),
        # costa y puente
        "p1": (1650, 800), "p2": (1740, 845), "p3": (1830, 880), "p4": (1900, 920), "p5": (1950, 985),
        "k1": (1687, 667), "k2": (1740, 647), "k3": (1807, 633), "k4": (1887, 613), "k5": (1940, 580),
    }
    for nombre, datos in nodos.items():
        m.agregar_nodo(nombre, datos[0], datos[1], datos[2] if len(datos) > 2 else None)
    m.conectar("rot_n", "rot_o", "rot_s", "rot_e", "rot_n")
    m.conectar("rot_n", "n1", "centro", "b1", "b3", "b2", "r1")
    m.conectar("r1", "pa", "pb", "prensa", "c4", "nw_e", "c5", "c6", "cruce_e")
    m.conectar("rot_e", "r1", "r2", "r3", "r4", "nw_e")
    m.conectar("rot_o", "w1", "w2", "w3", "w4", "d0", "oeste")
    m.conectar("d0", "d1", "parque", "d3", "d4", "d5")
    m.conectar("rot_s", "l1", "l2", "l3", "d4")
    m.conectar("d5", "s1", "alcaldia", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "cruce_e")
    m.conectar("s2", "se1", "se2", "se3", "se4")
    m.conectar("d0", "bn1", "barrio_norte", "bn2", "bn3", "j", "nw1", "nw2", "nw3", "nw4")
    m.conectar("j", "u1", "u2", "u3", "u4", "u5", "u6")
    m.conectar("cruce_e", "p1", "p2", "p3", "p4", "p5")
    m.conectar("cruce_e", "k1", "k2", "k3", "k4", "k5")
    return m
