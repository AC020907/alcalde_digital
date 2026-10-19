import random

from clases.RedCivitas import CANDIDATOS_ORIGEN, RUMORES

CONCLUSIONES = {
    "bot": "Una red de bots coordinada",
    "influencer": "Un influencer que buscaba seguidores",
    "ciudadano": "Un vecino que malinterpretó algo",
    "medio": "Un medio que publicó sin verificar",
}

# Cada rumor nace de una publicacion real e incompleta de una fuente confiable
# (indice alineado con RedCivitas.RUMORES). Es la base de la inferencia final.
CASOS_FUENTE = [
    {"autor": "@salud.nova",
     "real": "El Acueducto revisa la muestra 14 del Barrio Sur por turbidez. Repetirán el análisis hoy."},
    {"autor": "@salud.publica",
     "real": "El hospital central cerrará esta noche el ala de pediatría por fumigación. Urgencias atiende normal."},
    {"autor": "@alcaldia.nova",
     "real": "Por seguridad, dos puestos de votación del Barrio Norte cambian de sede. Consulte su puesto."},
    {"autor": "@noticias.nova",
     "real": "Los bancos cierran el lunes festivo. Cajeros y aplicación funcionan normal."},
]

INFERENCIAS = {
    "inventada": "La inventó desde cero",
    "recortada": "Recortó una publicación real y le cambió el sentido",
    "copiada": "Copió fielmente una fuente oficial",
}


class PuzzleEvidencias:
    """
    Minijuego Rastreador (puzzle): reconstruir en un tablero la cadena de difusion
    de un rumor, desde su origen hasta la publicacion viral.

    Estructura interna:
    - El rumor se propago con BFS (bfs_propagacion); el nivel de cada cuenta fija su hora.
    - La solucion es un camino en el grafo recorrido HACIA ATRAS con DFS: cada cuenta
      debe tener una arista hacia la siguiente (la sigue) y haber publicado antes.
    - dfs_buscar genera el caso, valida cualquier cadena correcta y calcula la pista.
    - El origen es siempre la cuenta que publico primero (nivel 0 del BFS).
    - Opcional: una inferencia final sobre la procedencia (la captura viral recorta una fuente real).
    """

    def __init__(self, grafo, semilla=0, eslabones=3, senuelos=3, tiempo=120.0,
                 comprobaciones=3, costo_pista=15.0, candidatos=None, inferencia=False,
                 rumor=None, hora_base=None):
        self.grafo = grafo
        self.semilla = semilla
        self.eslabones = eslabones
        self.tiempo_total = tiempo
        self.costo_pista = costo_pista
        self.comprobaciones = comprobaciones
        self.comprobaciones_usadas = 0
        self.pistas_usadas = 0
        self.transcurrido = 0.0
        self.empezado = False
        self.rumor = (semilla % len(RUMORES)) if rumor is None else rumor
        self.hora_base = 9 * 60 + 2 if hora_base is None else hora_base
        self.caso = dict(CASOS_FUENTE[self.rumor], viral=RUMORES[self.rumor])
        self._generar(candidatos or CANDIDATOS_ORIGEN, senuelos)
        self.slots = [None] * eslabones
        self.conclusion = None
        self.revision = [None] * eslabones     # True/False tras comprobar
        self.conclusion_ok = None
        self.explicaciones = []
        self.pista_carta = None
        self.candidatos_pista = []
        self.pista_receptor = None
        self.nivel_pista = 0
        self.seleccionada = None
        self.fase = "cadena"                   # "cadena" | "inferencia"
        self.inferencia_activa = inferencia
        self.inferencia_ok = False
        self.errores_inferencia = 0
        self.explicacion_inferencia = ""
        rng = random.Random("inferencia|%s" % semilla)
        self.opciones_inferencia = list(INFERENCIAS)
        rng.shuffle(self.opciones_inferencia)
        self.estado = "jugando"                # "victoria" | "derrota"
        self.motivo_fin = ""
        self.eventos = []
        self.version = 0                       # la UI recrea las cartas cuando cambia
        self.reloj = None

    # ===== GENERACION DEL CASO =====

    def _generar(self, candidatos, senuelos):
        rng = random.Random("puzzle|%s" % self.semilla)
        candidatos = [c for c in candidatos if self.grafo.existe(c)]
        for intento in range(200):
            origen = rng.choice(candidatos)
            niveles = self.grafo.bfs_propagacion(origen, semilla="%s|%d" % (self.semilla, intento),
                                                 factor=1.4, bloqueados={"jugador"})
            if len(niveles) <= self.eslabones:
                continue
            self.origen = origen
            self.minutos = {}
            for i, nivel in enumerate(niveles):
                for nodo in nivel:
                    self.minutos[nodo] = 0 if i == 0 else i * 7 + rng.randint(0, 4)
            for inicio in sorted(niveles[self.eslabones], key=self.grafo.alcance, reverse=True):
                ruta = self.ruta_desde(inicio)
                if len(ruta) == self.eslabones + 1:
                    self.inicio = inicio
                    self.solucion = ruta[1:]
                    self._elegir_senuelos(rng, senuelos)
                    return
        raise ValueError("No se pudo generar un tablero con semilla %s" % self.semilla)

    def _elegir_senuelos(self, rng, cantidad):
        cadena = set(self.solucion) | {self.inicio}
        cercanos = []
        for nodo in cadena:
            cercanos += [p for p in self.grafo.predecesores(nodo) if p in self.minutos and p not in cadena]
        lejanos = [n for n in self.minutos if n not in cadena and n not in cercanos]
        rng.shuffle(cercanos)
        rng.shuffle(lejanos)
        senuelos = []
        for nodo in cercanos + lejanos:
            if nodo not in senuelos and len(senuelos) < cantidad:
                senuelos.append(nodo)
        self.cartas = list(self.solucion) + senuelos
        rng.shuffle(self.cartas)
        tipo = self.tipo_origen()
        otras = [k for k in CONCLUSIONES if k != tipo]
        rng.shuffle(otras)
        self.opciones_conclusion = [tipo] + otras[:2]
        rng.shuffle(self.opciones_conclusion)

    def puede_ser_fuente(self, receptor, emisor):
        """Condicion del DFS: 'emisor' le envio el rumor a 'receptor' (lo sigue) y publico antes."""
        return (emisor in self.minutos and receptor in self.minutos and
                self.minutos[emisor] < self.minutos[receptor] and
                self.grafo.existe_conexion(emisor, receptor))

    def ruta_desde(self, nodo):
        camino, _ = self.grafo.dfs_buscar(nodo, self.origen, reverso=True, condicion=self.puede_ser_fuente)
        return camino

    def tipo_origen(self):
        tipo = self.grafo.tipo(self.origen)
        return tipo if tipo in CONCLUSIONES else "ciudadano"

    # ===== CONSULTAS PARA LA UI =====

    def hora(self, nodo):
        return self._formato(self.hora_base + self.minutos.get(nodo, 0))

    def hora_fuente_real(self):
        return self._formato(self.hora_base - 7)

    @staticmethod
    def _formato(total):
        return "%02d:%02d" % (total // 60 % 24, total % 60)

    def sigue_a(self, nodo):
        """Cuentas del tablero de las que 'nodo' recibe publicaciones (pista principal)."""
        en_tablero = set(self.cartas) | {self.inicio}
        return [p for p in self.grafo.predecesores(nodo) if p in en_tablero]

    def en_mesa(self):
        return [c for c in self.cartas if c not in self.slots]

    def restante(self):
        return max(0.0, self.tiempo_total - self.transcurrido)

    def comprobaciones_restantes(self):
        return self.comprobaciones - self.comprobaciones_usadas

    def jugando(self):
        return self.estado == "jugando" and self.empezado

    def terminado(self):
        return self.estado != "jugando"

    def exito(self):
        return self.estado == "victoria"

    def listo(self):
        return all(self.slots) and self.conclusion is not None and self.fase == "cadena"

    def ficha(self, nodo):
        perfil = self.grafo.perfil(nodo)
        return {"seguidores": perfil.get("seguidores", 0), "creada": perfil.get("creada", "?"),
                "verificada": perfil.get("verificada", False)}

    def costo_siguiente_pista(self):
        receptor, _ = self._primer_error()
        if receptor is not None and (self.pista_receptor != receptor or self.nivel_pista == 0):
            return self.costo_pista / 3
        return self.costo_pista if receptor is not None else self.costo_pista / 3

    # ===== ACCIONES =====

    def empezar(self):
        self.empezado = True

    def colocar(self, carta, indice):
        """Pone 'carta' en el hueco 'indice'. Devuelve la carta desplazada (vuelve a la mesa) o None."""
        if not self.jugando() or self.fase != "cadena" or carta not in self.cartas or not 0 <= indice < self.eslabones:
            return None
        if carta in self.slots:
            self.slots[self.slots.index(carta)] = None
        desplazada = self.slots[indice]
        self.slots[indice] = carta
        self._cambio()
        return desplazada

    def quitar(self, carta):
        if self.fase == "cadena" and carta in self.slots:
            self.slots[self.slots.index(carta)] = None
        self._cambio()

    def _cambio(self):
        self.revision = [None] * self.eslabones
        self.explicaciones = []
        self.seleccionada = None
        self.version += 1

    def elegir_conclusion(self, clave):
        if self.jugando() and self.fase == "cadena" and clave in self.opciones_conclusion:
            self.conclusion = clave
            self.conclusion_ok = None

    def comprobar(self):
        if not self.jugando() or not self.listo():
            return False
        self.comprobaciones_usadas += 1
        self.explicaciones = []
        receptor = self.inicio
        for i, carta in enumerate(self.slots):
            ultimo = i == self.eslabones - 1
            self.revision[i] = self.puede_ser_fuente(receptor, carta) and (not ultimo or carta == self.origen)
            if not self.revision[i]:
                self.explicaciones.append(self._explicar(receptor, carta, ultimo))
            receptor = carta
        self.conclusion_ok = self.conclusion == self.tipo_origen()
        if all(self.revision) and not self.conclusion_ok:
            ficha = self.ficha(self.origen)
            self.explicaciones.append(
                "La ficha del origen (creada %s, %s seguidores%s) no encaja con '%s'." % (
                    ficha["creada"], "{:,}".format(ficha["seguidores"]).replace(",", "."), ", verificada" if ficha["verificada"] else ", sin verificar",
                    CONCLUSIONES[self.conclusion].lower()))
        if all(self.revision) and self.conclusion_ok:
            if self.inferencia_activa:
                self.fase = "inferencia"
                self.eventos.append(("inferencia", None))
            else:
                self._victoria()
        elif self.comprobaciones_restantes() <= 0:
            self._terminar_derrota("Te quedaste sin comprobaciones.")
        else:
            self.eventos.append(("error", sum(1 for r in self.revision if r)))
        return True

    def _explicar(self, receptor, emisor, ultimo):
        if emisor == receptor:
            return "%s no puede ser su propia fuente." % emisor
        if self.minutos[emisor] >= self.minutos[receptor]:
            relacion = "a la misma hora que" if self.minutos[emisor] == self.minutos[receptor] else "después de"
            return "%s publicó a las %s, %s %s (%s): no pudo ser su fuente." % (
                emisor, self.hora(emisor), relacion, receptor, self.hora(receptor))
        if not self.grafo.existe_conexion(emisor, receptor):
            return "%s no sigue a %s: nunca vio sus publicaciones." % (receptor, emisor)
        if ultimo:
            return "%s encaja, pero no es quien publicó primero: alguien se lo envió antes." % emisor
        return "%s no encaja en ese lugar." % emisor

    def responder_inferencia(self, clave):
        if self.estado != "jugando" or self.fase != "inferencia" or clave not in INFERENCIAS:
            return False
        if clave == "recortada":
            self.inferencia_ok = True
            self._victoria()
            return True
        self.errores_inferencia += 1
        if clave == "inventada":
            self.explicacion_inferencia = ("La captura viral tiene la tipografía y la hora de %s: partió de algo real." %
                                           self.caso["autor"])
        else:
            self.explicacion_inferencia = ("La fuente original no dice lo mismo: la captura viral le quitó el final y "
                                           "cambió el sentido.")
        self.eventos.append(("error_inferencia", None))
        return False

    def ruta_tablero(self, receptor, pasos, usados=()):
        """DFS restringido a las fichas del tablero: 'pasos' cuentas desde receptor hasta el origen."""
        if pasos == 0:
            return [] if receptor == self.origen else None
        for carta in self.cartas:
            if carta not in usados and self.puede_ser_fuente(receptor, carta):
                resto = self.ruta_tablero(carta, pasos - 1, tuple(usados) + (carta,))
                if resto is not None:
                    return [carta] + resto
        return None

    def _primer_error(self):
        """(receptor, indice) del primer hueco vacio o que ya no lleva al origen, desde la publicacion viral."""
        receptor = self.inicio
        for i in range(self.eslabones):
            carta = self.slots[i]
            usados = tuple(c for c in self.slots[:i + 1] if c)
            if (carta is None or not self.puede_ser_fuente(receptor, carta) or
                    self.ruta_tablero(carta, self.eslabones - 1 - i, usados) is None):
                return receptor, i
            receptor = carta
        return None, None

    def pedir_pista(self):
        """Nivel 1: senala las fuentes posibles del eslabon. Nivel 2: revela la cuenta (DFS)."""
        if not self.jugando() or self.fase != "cadena":
            return None
        receptor, indice = self._primer_error()
        if receptor is None:
            self._gastar(self.costo_pista / 3)
            self.eventos.append(("pista_conclusion", None))
            return None
        anteriores = tuple(c for c in self.slots[:indice] if c)
        if self.pista_receptor != receptor:
            self.pista_receptor = receptor
            self.nivel_pista = 0
        if self.nivel_pista == 0:
            self.candidatos_pista = [p for p in self.sigue_a(receptor)
                                     if p in self.cartas and self.minutos[p] < self.minutos[receptor]]
            self.nivel_pista = 1
            self._gastar(self.costo_pista / 3)
            self.eventos.append(("pista1", receptor))
            return receptor
        ruta = self.ruta_tablero(receptor, self.eslabones - indice, anteriores)
        if not ruta:
            return None
        self.pista_carta = ruta[0]
        self.nivel_pista = 2
        self._gastar(self.costo_pista)
        self.eventos.append(("pista", self.pista_carta))
        return self.pista_carta

    def _gastar(self, segundos):
        self.pistas_usadas += 1
        self.transcurrido += segundos
        self._revisar_tiempo()

    def tick(self, dt):
        if self.jugando() and self.fase == "cadena":
            self.transcurrido += dt
            self._revisar_tiempo()

    def tick_reloj(self, ahora):
        """Avanza con el reloj real; el tope evita saltos al volver de un menu o de cargar partida."""
        ultimo = getattr(self, "reloj", None)
        if ultimo is not None:
            self.tick(min(1.0, max(0.0, ahora - ultimo)))
        self.reloj = ahora if self.jugando() else None

    def _revisar_tiempo(self):
        if self.estado == "jugando" and self.transcurrido >= self.tiempo_total:
            self._terminar_derrota("Se acabó el tiempo.")

    def _victoria(self):
        self.estado = "victoria"
        self.motivo_fin = "Cadena reconstruida: el rumor empezó en %s." % self.grafo.nombre(self.origen)
        self.eventos.append(("victoria", None))

    def _terminar_derrota(self, motivo):
        self.estado = "derrota"
        self.motivo_fin = "%s El rumor empezó en %s." % (motivo, self.grafo.nombre(self.origen))
        self.eventos.append(("derrota", None))

    # ===== RESULTADO =====

    def calificacion(self):
        if not self.exito():
            return "D"
        if self.comprobaciones_usadas == 1 and self.pistas_usadas == 0:
            return "S" if self.errores_inferencia == 0 else "A"
        if self.comprobaciones_usadas <= 2 and self.pistas_usadas == 0:
            return "A"
        if self.pistas_usadas <= 2:
            return "B"
        return "C"

    def resultado(self):
        nota = self.calificacion()
        if nota in ("S", "A"):
            consecuencia = {"desinformacion": -8, "confianza": 5, "info_verificada": 5, "reputacion": 8, "puntos": 16}
        elif self.exito():
            consecuencia = {"desinformacion": -5, "confianza": 3, "info_verificada": 3, "reputacion": 4, "puntos": 10}
        else:
            consecuencia = {"desinformacion": 4, "confianza": -3, "reputacion": -4}
        return {
            "minijuego": "rastreador",
            "exito": self.exito(),
            "calificacion": nota,
            "origen": self.origen,
            "comprobaciones": self.comprobaciones_usadas,
            "pistas": self.pistas_usadas,
            "inferencia": self.inferencia_ok,
            "mensaje": self.motivo_fin,
            "consecuencia": consecuencia,
        }
