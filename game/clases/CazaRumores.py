from collections import deque
import random

from clases.ConfigMinijuegos import ARCADE, MODOS, REPOSTS_POR_ALCANCE


class Paquete:
    """Un rumor viajando por una conexion del grafo (lo que el jugador intercepta)."""

    def __init__(self, origen, destino, duracion):
        self.origen = origen
        self.destino = destino
        self.duracion = duracion
        self.progreso = 0.0


class CazaRumores:
    """
    Motor de Contencion / Gran Viralizacion en tiempo real.

    Estructura interna - BFS en tiempo real sobre el grafo dirigido y pesado:
    - 'cola' es la cola FIFO del BFS: cada cuenta contagiada entra a la cola y,
      cuando le toca, envia el rumor a sus seguidores (vecinos).
    - 'en_camino' + estados evitan enviar dos veces al mismo usuario (visitados).
    - Cada envio es un Paquete que tarda segun el peso de la conexion; si el
      jugador lo intercepta, esa rama del recorrido se corta.
    """

    def __init__(self, grafo, modo, focos, semilla=0, config=None, inmunes=("jugador",)):
        self.cfg = dict(ARCADE)
        self.cfg.update(MODOS.get(modo, {}))
        self.cfg.update(config or {})
        self.grafo = grafo
        self.modo = modo
        self.semilla = semilla
        self.rng = random.Random("arcade|%s|%s" % (modo, semilla))
        self.inmunes = set(inmunes)

        self.estado_nodo = {}
        for nodo in grafo.lista_nodos():
            self.estado_nodo[nodo] = "inmune" if nodo in self.inmunes else "sano"
        self.cola = deque()
        self.en_camino = set()
        self.paquetes = []
        self.padre = {}
        self.hora = {}

        self.reloj = 0.0               # tiempo de simulacion
        self.transcurrido = 0.0        # tiempo de juego (sin cuenta regresiva)
        self.intro = self.cfg["cuenta_regresiva"]
        self.reposts = 0.0
        self.reposts_base = 0.0        # la viralidad se mide desde aqui
        self.puntos = 0
        self.combo = 0
        self.mejor_combo = 0
        self.interceptados = 0
        self.contagios = 0
        self.enviados = 0
        self.cuarentenas = 0
        self.ondas = self.cfg["ondas_iniciales"]
        self.cooldown = 0.0
        self.proximo_evento = self.cfg["intervalo_evento"]
        self.proximo_foco = self.cfg["intervalo_foco"]
        self.fin_cuarentena = {}
        self._ultimo_evento = None
        self._avisos = set()
        self.eventos = []              # mensajes para la vista: dicts con "tipo"
        self.estado = "jugando"        # "victoria" | "derrota"
        self.motivo_fin = ""

        for foco in focos:
            if self.estado_nodo.get(foco) == "sano":
                self._contagiar(foco, None, silencioso=True)

    # ===== CONSULTAS =====

    def terminado(self):
        return self.estado != "jugando"

    def exito(self):
        return self.estado == "victoria"

    def jugando(self):
        return self.estado == "jugando" and self.intro <= 0

    def viralidad(self):
        return min(1.0, (self.reposts - self.reposts_base) / self.cfg["umbral_viral"])

    def tiempo_restante(self):
        return max(0.0, self.cfg["duracion"] - self.transcurrido)

    def activos(self):
        return [n for n, e in self.estado_nodo.items() if e == "infectado"]

    def velocidad(self):
        return 1.0 + self.cfg["aceleracion"] * min(1.0, self.transcurrido / self.cfg["duracion"])

    def edad(self, nodo):
        return self.reloj - self.hora[nodo] if nodo in self.hora else 0.0

    def potencial(self, nodo):
        sanos = [v for v in self.grafo.vecinos(nodo) if self.estado_nodo[v] == "sano"]
        return int(sum(self.grafo.alcance(v) for v in sanos) * REPOSTS_POR_ALCANCE)

    def _evento(self, tipo, **datos):
        datos["tipo"] = tipo
        self.eventos.append(datos)

    # ===== BUCLE PRINCIPAL =====

    def actualizar(self, dt):
        if self.estado != "jugando":
            return
        if self.intro > 0:
            self.intro -= dt
            return
        self.transcurrido += dt
        self.cooldown = max(0.0, self.cooldown - dt)
        self._simular(dt)
        self._liberar_cuarentenas()
        if self.cfg["intervalo_foco"] and self.transcurrido >= self.proximo_foco:
            self.proximo_foco += self.cfg["intervalo_foco"]
            self._nuevo_foco()
        if self.transcurrido >= self.proximo_evento:
            self.proximo_evento += self.cfg["intervalo_evento"]
            self._lanzar_evento()
        self._revisar_umbrales()
        self._revisar_fin()

    def _simular(self, dt):
        self.reloj += dt
        self._mover_paquetes(dt)
        self._perder_interes()
        self._procesar_cola()
        for nodo in self.activos():
            self.reposts += self.grafo.alcance(nodo) * REPOSTS_POR_ALCANCE * self.cfg["reposts_por_segundo"] * dt

    def _mover_paquetes(self, dt):
        avance = dt * self.velocidad()
        for paquete in list(self.paquetes):
            paquete.progreso += avance / paquete.duracion
            if paquete.progreso >= 1.0:
                self.paquetes.remove(paquete)
                self.en_camino.discard(paquete.destino)
                self._llegada(paquete)

    def _perder_interes(self):
        """Modelo SIS: tras un tiempo compartiendo, la cuenta se aburre y vuelve a estar sana."""
        limite = self.cfg["duracion_contagio"]
        if not limite:
            return
        for nodo in self.activos():
            if self.reloj - self.hora[nodo] >= limite:
                self.estado_nodo[nodo] = "sano"

    def _llegada(self, paquete):
        estado = self.estado_nodo[paquete.destino]
        if estado == "sano":
            self.combo = 0
            self._contagiar(paquete.destino, paquete.origen)
        elif estado in ("protegido", "cuarentena"):
            self._evento("bloqueado", nodo=paquete.destino)

    def _procesar_cola(self):
        """Atiende la cola FIFO: cada cuenta lista envia el rumor a sus seguidores sanos."""
        for _ in range(len(self.cola)):
            nodo, listo = self.cola.popleft()
            if self.estado_nodo[nodo] != "infectado":
                continue
            if listo > self.reloj:
                self.cola.append((nodo, listo))
                continue
            quedan_sanos = False
            for vecino in self.grafo.vecinos(nodo):
                if self.estado_nodo[vecino] != "sano" or vecino in self.en_camino:
                    continue
                quedan_sanos = True
                probabilidad = min(1.0, self.grafo.peso(nodo, vecino) * self.cfg["prob_envio"])
                if self.rng.random() < probabilidad:
                    self._enviar(nodo, vecino)
            if quedan_sanos:
                self.cola.append((nodo, self.reloj + self.cfg["reemision"]))

    def _enviar(self, origen, destino, rapido=False):
        duracion = self.cfg["tiempo_viaje"] / (0.5 + self.grafo.peso(origen, destino))
        if rapido:
            duracion *= 0.6
        self.en_camino.add(destino)
        self.paquetes.append(Paquete(origen, destino, duracion))
        self.enviados += 1

    def _contagiar(self, nodo, padre, silencioso=False):
        self.estado_nodo[nodo] = "infectado"
        self.padre[nodo] = padre
        self.hora[nodo] = self.reloj
        ganados = self.grafo.alcance(nodo) * REPOSTS_POR_ALCANCE
        self.reposts += ganados
        self.contagios += 1
        self.cola.append((nodo, self.reloj + self.cfg["retardo_emision"]))
        if not silencioso:
            self._evento("contagio", nodo=nodo, reposts=ganados)

    # ===== ACCIONES DEL JUGADOR =====

    def interceptar(self, paquete):
        if not self.jugando() or paquete not in self.paquetes:
            return 0
        self.paquetes.remove(paquete)
        self.en_camino.discard(paquete.destino)
        self.interceptados += 1
        self.combo = min(self.cfg["max_combo"], self.combo + 1)
        self.mejor_combo = max(self.mejor_combo, self.combo)
        ganados = self.cfg["puntos_intercepcion"] * self.combo
        self.puntos += ganados
        if self.interceptados % self.cfg["intercepciones_por_onda"] == 0 and self.ondas < self.cfg["max_ondas"]:
            self.ondas += 1
            self._evento("onda_lista")
        return ganados

    def puede_cuarentena(self, nodo):
        return self.jugando() and self.cooldown <= 0 and self.estado_nodo.get(nodo) == "infectado"

    def cuarentena(self, nodo):
        if not self.puede_cuarentena(nodo):
            return False
        evitados = self.potencial(nodo)
        self.estado_nodo[nodo] = "cuarentena"
        self.fin_cuarentena[nodo] = self.transcurrido + self.cfg["duracion_cuarentena"]
        self.cooldown = self.cfg["cooldown_cuarentena"]
        self.cuarentenas += 1
        self.puntos += self.cfg["puntos_cuarentena"]
        self._evento("cuarentena", nodo=nodo, evitados=evitados)
        return True

    def onda(self, paquetes):
        """Onda de verificacion: elimina los rumores que la vista detecto dentro del radio."""
        if not self.jugando() or self.ondas <= 0:
            return 0
        self.ondas -= 1
        eliminados = 0
        for paquete in paquetes:
            if paquete in self.paquetes:
                self.paquetes.remove(paquete)
                self.en_camino.discard(paquete.destino)
                eliminados += 1
        self.interceptados += eliminados
        self.puntos += eliminados * self.cfg["puntos_intercepcion"]
        self._evento("onda", eliminados=eliminados)
        return eliminados

    def _liberar_cuarentenas(self):
        for nodo, fin in list(self.fin_cuarentena.items()):
            if self.transcurrido >= fin:
                del self.fin_cuarentena[nodo]
                if self.estado_nodo[nodo] == "cuarentena":
                    self.estado_nodo[nodo] = "infectado"
                    self.cola.append((nodo, self.reloj + self.cfg["retardo_emision"]))
                    self._evento("cuarentena_fin", nodo=nodo)

    def _nuevo_foco(self):
        candidatos = [n for n in self.grafo.lista_nodos()
                      if self.estado_nodo[n] == "sano" and n not in self.en_camino
                      and self.grafo.tipo(n) in ("bot", "ciudadano")]
        if candidatos:
            nodo = self.rng.choice(candidatos)
            self._contagiar(nodo, None)
            self._evento("foco", nodo=nodo)

    # ===== EVENTOS ALEATORIOS =====

    def _sanos(self, tipo):
        return [n for n in self.grafo.lista_nodos()
                if self.estado_nodo[n] == "sano" and self.grafo.tipo(n) == tipo and n not in self.en_camino]

    def _barrio(self, nodo):
        return self.grafo.perfil(nodo).get("barrio", "")

    def _lanzar_evento(self):
        posibles = []
        if self._sanos("influencer"):
            posibles.append("influencer")
        if self._sanos("bot"):
            posibles.append("botnet")
        if self._sanos("medio"):
            posibles.append("medio")
        afectados = set(self._barrio(n) for n, e in self.estado_nodo.items() if e in ("infectado", "cuarentena"))
        limpios = [n for n in self._sanos("ciudadano") if self._barrio(n) not in afectados]
        if limpios:
            posibles.append("captura")
        posibles = [p for p in posibles if p != self._ultimo_evento]
        if not posibles:
            return
        clave = self.rng.choice(posibles)
        self._ultimo_evento = clave

        if clave == "influencer":
            nodo = self.rng.choice(self._sanos("influencer"))
            self._contagiar(nodo, None)
            for vecino in self.grafo.vecinos(nodo):
                if self.estado_nodo[vecino] == "sano" and vecino not in self.en_camino:
                    self._enviar(nodo, vecino, rapido=True)
            self._evento("banner", titulo="INFLUENCER COMPARTE EL RUMOR",
                         texto="%s lo publico: rafaga de reposts" % self.grafo.nombre(nodo), malo=True)
        elif clave == "botnet":
            bots = self._sanos("bot")
            self.rng.shuffle(bots)
            for nodo in bots[:2]:
                self._contagiar(nodo, None)
            self._evento("banner", titulo="BOTNET DETECTADA",
                         texto="%d cuentas falsas empiezan a compartir" % len(bots[:2]), malo=True)
        elif clave == "medio":
            nodo = self.rng.choice(self._sanos("medio"))
            self.estado_nodo[nodo] = "protegido"
            for vecino in self.grafo.vecinos(nodo):
                if self.estado_nodo[vecino] == "sano":
                    self.estado_nodo[vecino] = "protegido"
            self.reposts *= 0.85
            self._evento("banner", titulo="MEDIO OFICIAL DESMIENTE",
                         texto="%s y sus seguidores quedan protegidos  -15%% viralidad" % self.grafo.nombre(nodo), malo=False)
        else:
            nodo = self.rng.choice(limpios)
            self._contagiar(nodo, None)
            self._evento("banner", titulo="CAPTURA FUERA DE CONTEXTO",
                         texto="Nuevo foco en %s" % self._barrio(nodo).upper(), malo=True)

    # ===== FIN DE PARTIDA =====

    def _revisar_umbrales(self):
        v = self.viralidad()
        if v >= 0.85 and "critico" not in self._avisos:
            self._avisos.update(("critico", "tendencia"))
            self._evento("banner", titulo="VIRALIDAD CRITICA", texto="Estas a punto de perder el control", malo=True)
        elif v >= 0.6 and "tendencia" not in self._avisos:
            self._avisos.add("tendencia")
            self._evento("banner", titulo="TENDENCIA #1 EN CIVITAS", texto="El rumor esta en todas partes", malo=True)

    def _terminar(self, estado, motivo):
        self.estado = estado
        self.motivo_fin = motivo
        self._evento("fin", exito=(estado == "victoria"))

    def _revisar_fin(self):
        if self.estado != "jugando":
            return
        if self.viralidad() >= 1.0:
            self._terminar("derrota", "El rumor se volvio VIRAL con %d reposts." % self.reposts)
        elif self.transcurrido >= self.cfg["duracion"]:
            self.puntos += self.cfg["bono_contencion"]
            self._terminar("victoria", "Resististe la crisis: Civitas sigue bajo control.")

    # ===== RESULTADO =====

    def calificacion(self):
        if not self.exito():
            return "D"
        v = self.viralidad()
        if v < 0.35:
            return "S"
        if v < 0.55:
            return "A"
        if v < 0.75:
            return "B"
        return "C"

    def resultado(self):
        nota = self.calificacion()
        if nota in ("S", "A"):
            consecuencia = {"desinformacion": -7, "confianza": 4, "conflictos": -3, "puntos": 14}
        elif nota in ("B", "C"):
            consecuencia = {"desinformacion": -3, "confianza": 2, "puntos": 7}
        else:
            consecuencia = {"desinformacion": 7, "conflictos": 4, "confianza": -4}
        return {
            "minijuego": "viralizacion" if self.modo == "viral" else "contencion",
            "exito": self.exito(),
            "calificacion": nota,
            "puntos": self.puntos,
            "reposts": int(self.reposts),
            "interceptados": self.interceptados,
            "mejor_combo": self.mejor_combo,
            "mensaje": self.motivo_fin,
            "consecuencia": consecuencia,
        }


def focos_viralizacion(grafo, origen, semilla, oleadas):
    """La Gran Viralizacion arranca con las primeras oleadas ya calculadas por BFS."""
    niveles = grafo.bfs_propagacion(origen, semilla="viral|%s" % semilla, factor=1.2, bloqueados={"jugador"})
    return [n for nivel in niveles[:oleadas] for n in nivel]
