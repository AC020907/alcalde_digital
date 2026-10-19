import random

from clases.CazaRumores import CazaRumores
from clases.RedCivitas import CANDIDATOS_ORIGEN


class RastreoEnVivo(CazaRumores):
    """
    Minijuego 1 - Rastreador en vivo. El rumor se sigue propagando (BFS en
    tiempo real del motor base) mientras el jugador persigue su rastro hacia
    atras hasta la cuenta que lo inicio.

    Estructura interna - DFS:
    - 'rastro' es una pila: cada cuenta correcta se apila (bajar un nivel mas
      profundo en la cadena) y el clic derecho desapila (retroceder).
    - Una cuenta solo es valida si le envio el rumor a la cima de la pila
      ANTES de que esta lo recibiera (condicion del recorrido).
    - dfs_buscar (reverso) calcula la pista y cuantos saltos faltan.
    """

    def __init__(self, grafo, semilla=0, candidatos=None, config=None):
        rng = random.Random("origen|%s" % semilla)
        candidatos = [c for c in (candidatos or CANDIDATOS_ORIGEN) if grafo.existe(c)]
        self.origen = rng.choice(candidatos)
        CazaRumores.__init__(self, grafo, "rastreo", [self.origen], semilla, config)
        self._precalentar()
        self.reposts_base = self.reposts

        self.inicio = max((n for n in self.hora if n != self.origen),
                          key=lambda n: (self.profundidad(n), self.grafo.alcance(n)))
        self.rastro = [self.inicio]
        self.pistas_falsas = 0
        self.pistas_usadas = 0
        self.pista_nodo = None
        self.pista_hasta = 0.0

    def _precalentar(self):
        """El rumor ya lleva un rato circulando cuando el jugador empieza."""
        objetivo = self.cfg["precalentamiento"]
        paso = 0.1
        while self.reloj < objetivo * 3:
            self._simular(paso)
            if self.reloj >= objetivo and max(self.profundidad(n) for n in self.hora) >= 3:
                break

    def profundidad(self, nodo):
        saltos = 0
        while self.padre.get(nodo) is not None:
            nodo = self.padre[nodo]
            saltos += 1
        return saltos

    # ===== DFS DEL RASTRO =====

    def actual(self):
        return self.rastro[-1]

    def puede_ser_fuente(self, receptor, emisor):
        return (emisor in self.hora and receptor in self.hora and
                self.hora[emisor] < self.hora[receptor] and
                self.grafo.existe_conexion(emisor, receptor))

    def ruta_al_origen(self):
        camino, _ = self.grafo.dfs_buscar(self.actual(), self.origen, reverso=True,
                                          condicion=self.puede_ser_fuente)
        return camino

    def saltos_restantes(self):
        return max(0, len(self.ruta_al_origen()) - 1)

    def rastrear(self, nodo):
        if not self.jugando() or nodo in self.rastro:
            return False
        if self.puede_ser_fuente(self.actual(), nodo):
            self.rastro.append(nodo)
            self.pista_nodo = None
            ganados = self.cfg["puntos_rastro"] * len(self.rastro)
            self.puntos += ganados
            self._evento("rastro", nodo=nodo, puntos=ganados)
            if nodo == self.origen:
                self.puntos += self.cfg["bono_contencion"]
                self._terminar("victoria", "Encontraste a %s: inicio el rumor." % self.grafo.nombre(nodo))
            return True
        self.pistas_falsas += 1
        self.combo = 0
        self.transcurrido += self.cfg["penalizacion_rastro"]
        motivo = "no compartio el rumor" if nodo not in self.hora else "no se lo envio"
        self._evento("rastro_falso", nodo=nodo, motivo=motivo)
        return False

    def volver(self):
        if not self.jugando() or len(self.rastro) <= 1:
            return False
        self.rastro.pop()
        return True

    def pedir_pista(self):
        if not self.jugando():
            return False
        camino = self.ruta_al_origen()
        if len(camino) < 2:
            return False
        self.pistas_usadas += 1
        self.transcurrido += self.cfg["costo_pista"]
        self.pista_nodo = camino[1]
        self.pista_hasta = self.transcurrido + 3.0
        self._evento("pista", nodo=self.pista_nodo)
        return True

    # ===== FIN =====

    def _revisar_fin(self):
        if self.estado != "jugando":
            return
        if self.viralidad() >= 1.0:
            self._terminar("derrota", "El rumor se volvio VIRAL antes de encontrar el origen. Era %s." % self.grafo.nombre(self.origen))
        elif self.transcurrido >= self.cfg["duracion"]:
            self._terminar("derrota", "Se acabo el tiempo. El origen era %s." % self.grafo.nombre(self.origen))

    def calificacion(self):
        if not self.exito():
            return "D"
        if self.pistas_falsas == 0 and self.pistas_usadas == 0:
            return "S"
        if self.pistas_falsas <= 1 and self.pistas_usadas == 0:
            return "A"
        if self.pistas_falsas <= 3:
            return "B"
        return "C"

    def resultado(self):
        r = CazaRumores.resultado(self)
        r["minijuego"] = "rastreador"
        r["origen"] = self.origen
        r["pistas_falsas"] = self.pistas_falsas
        if r["calificacion"] in ("S", "A"):
            r["consecuencia"] = {"desinformacion": -8, "confianza": 5, "info_verificada": 5, "reputacion": 8, "puntos": 16}
        elif r["exito"]:
            r["consecuencia"] = {"desinformacion": -5, "confianza": 3, "info_verificada": 3, "reputacion": 4, "puntos": 10}
        else:
            r["consecuencia"] = {"desinformacion": 4, "confianza": -3, "reputacion": -4}
        return r
