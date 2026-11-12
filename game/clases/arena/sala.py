"""
Sala de Arena independiente del transporte (la usa la Arena Online por HTTPS).

Envuelve la misma Partida de reglas.py (unica fuente de verdad) y anade lo que necesita una sala online:
codigo, tokens secretos por jugador, anfitrion, "listo", reloj autoritativo, presencia (sin peticiones en
PRESENCIA_S segundos = desconectado), reconexion con el mismo token, jugadores automaticos e idempotencia
por id de mensaje. El tiempo avanza de forma perezosa: cada peticion llama a tick(), asi no hacen falta
hilos en el servidor web y el estado es igual de autoritativo.

Dos formatos:
- clasica: solo las rondas del Consejo Civico (fases ronda -> resultado -> ... -> final).
- campana (por defecto): una historia compartida con cuatro perspectivas (campana.py). Cada ronda es
      escena -> reto -> reto_resultado -> ronda (decision civica) -> resultado (consecuencia)
  y los retos son los cinco minijuegos, que juegan TODOS: Moderacion, Rastreador, Caza-Rumores, Ruta de la
  Verdad (plataformas) y Duelo de Frecuencias (final). El servidor decide semilla y escenario, y puntua:
      moderador   -> cada decision llega al servidor, que la juzga con ColaModeracion (el cliente no sabe quien es bot);
      rastreador  -> el tablero vive en el servidor (PuzzleEvidencias); el cliente pide comprobar y pedir pista;
      contencion  -> el cliente envia sus intercepciones y el servidor rejuega la propagacion (caza_web);
      plataformas -> el cliente envia su traza de entradas y el servidor rejuega la carrera (Plataformas);
      ritmo       -> juicio y desvio por nota, validados contra el chart y el reloj de la sala (duelo_online).
"""
import random
import secrets
import threading
import time

from clases import Plataformas as PL
from clases.Moderador import ColaModeracion
from clases.PuzzleEvidencias import PuzzleEvidencias, CONCLUSIONES
from clases.RedCivitas import crear_red_civitas
from clases.arena import campana as CA
from clases.arena import caza_web as CW
from clases.arena import duelo_online as DO
from clases.arena import torneo as T
from clases.arena.bot import elegir_ruta
from clases.arena.reglas import Partida, ROLES, MIN_JUGADORES, MAX_JUGADORES, NOMBRE_ROL, NOMBRE_INDICADOR
from clases.moderacion_datos import publicaciones_moderacion

PRESENCIA_S = 20.0
PAUSA_RESULTADO_S = 10.0
PAUSA_RETO_S = 14.0
PREPARACION_S = 5.0            # cuenta atras comun antes de cada reto (el Duelo usa la suya, mas larga)
MARGEN_ENTREGA_S = 12.0
SEG_POR_COMENTARIO = 6.0


class ErrorSala(Exception):
    def __init__(self, codigo, mensaje):
        super(ErrorSala, self).__init__(mensaje)
        self.codigo, self.mensaje = codigo, mensaje


class SalaArena(object):
    def __init__(self, codigo, semilla=None, rondas=5, segundos=25, reloj=time.monotonic, campana=True, modo="feria",
                 modo_duelo=None):
        self.codigo = codigo
        self.reloj = reloj
        self.lock = threading.RLock()
        self.partida = Partida(semilla if semilla is not None else random.randrange(10 ** 9), rondas, segundos)
        self.tokens = {}            # token -> jid
        self.visto = {}             # jid -> ultimo instante en que pidio algo
        self.bots = {}              # jid -> [rng, instante en que decidira en esta ronda]
        self.listos = set()
        self.anfitrion = None
        self.ids_vistos = {}        # jid -> set(id de mensaje)
        self.limite = None
        self.restante_pausa = None
        self.siguiente_en = None
        self.creada = self.ultima_actividad = reloj()
        self.version = 0            # crece con cada cambio: el cliente evita redibujar si no cambio
        self.campana = bool(campana)
        self.modo = modo if modo in T.MODOS_TORNEO else "feria"
        self.modo_duelo = modo_duelo or T.MODOS_TORNEO[self.modo]["ritmo"]["modo"]
        self.guion = CA.rondas(rondas) if self.campana else ()
        self.reto = None            # reto en curso (dict) o None
        self.retos = []             # resumen de cada reto terminado
        self.puntos_reto = {}       # jid -> {clave: resultado}
        self.escena_fin = None
        self.idx = 0                # ronda de la campana en curso (indice en self.guion)
        self.escena_listos = set()
        self.torneo_final = False

    # ---------- utilidades ----------
    def _jid(self, token):
        jid = self.tokens.get(token)
        if jid is None:
            raise ErrorSala("token", "No perteneces a esta sala.")
        self.visto[jid] = self.reloj()
        self.partida.jugadores[jid].conectado = True
        return jid

    def _tocar(self):
        self.version += 1
        self.ultima_actividad = self.reloj()

    def _repetido(self, jid, mid):
        if not mid:
            return False
        vistos = self.ids_vistos.setdefault(jid, set())
        if mid in vistos:
            return True
        vistos.add(mid)
        return False

    def _humanos(self):
        return [jid for jid, j in self.partida.jugadores.items() if jid not in self.bots and j.conectado]

    def _anfitrion(self, token, accion):
        jid = self._jid(token)
        if jid != self.anfitrion:
            raise ErrorSala("permiso", "Solo el anfitrión puede %s." % accion)
        return jid

    # ---------- lobby ----------
    def unir(self, nombre, rol, bot=False):
        with self.lock:
            self.tick()
            jid = "j%d" % (len(self.tokens) + 1)
            error = self.partida.unir(jid, nombre, rol)
            if error:
                codigo = "llena" if "llena" in error else ("empezada" if "empez" in error else "rol")
                raise ErrorSala(codigo, error)
            token = secrets.token_urlsafe(18)
            self.tokens[token] = jid
            self.visto[jid] = self.reloj()
            if bot:
                self.bots[jid] = [random.Random("%s|%s" % (self.partida.semilla, jid)), None]
                self.listos.add(jid)
            elif self.anfitrion is None:
                self.anfitrion = jid
            self._tocar()
            return jid, token

    def agregar_bots(self, token):
        """El anfitrion completa la sala con jugadores automaticos (roles libres)."""
        with self.lock:
            self._anfitrion(token, "añadir jugadores automáticos")
            libres = [r for r in ROLES if r not in {j.rol for j in self.partida.jugadores.values()}]
            for rol in libres[:MAX_JUGADORES - len(self.partida.jugadores)]:
                self.unir("%s (bot)" % NOMBRE_ROL[rol], rol, bot=True)

    def listo(self, token, valor):
        with self.lock:
            jid = self._jid(token)
            (self.listos.add if valor else self.listos.discard)(jid)
            self._tocar()

    def empezar(self, token):
        with self.lock:
            self._anfitrion(token, "empezar")
            if not self.partida.puede_empezar():
                raise ErrorSala("jugadores", "Se necesitan de %d a %d jugadores." % (MIN_JUGADORES, MAX_JUGADORES))
            faltan = set(self.partida.jugadores) - self.listos - {self.anfitrion}
            if faltan:
                raise ErrorSala("listos", "Faltan jugadores por marcar «Listo».")
            self._siguiente_ronda()

    def _siguiente_ronda(self):
        if self.campana:
            self._abrir_escena()
        else:
            self._abrir_ronda()

    # ---------- escena (historia compartida + pista privada) ----------
    def _guion_actual(self):
        return self.guion[self.idx]

    def _abrir_escena(self):
        self.idx = min(self.partida.ronda, len(self.guion) - 1)
        self.partida.fase = "escena"
        self.escena_fin = self.reloj() + CA.SEGUNDOS_ESCENA
        self.escena_listos = set()
        self.limite = self.siguiente_en = None
        self._tocar()

    def escena_lista(self, token):
        with self.lock:
            jid = self._jid(token)
            if self.partida.fase == "escena":
                self.escena_listos.add(jid)
                self._tocar()
                self.tick()

    # ---------- reto (minijuego competitivo) ----------
    def _abrir_reto(self):
        p = self.partida
        g = self._guion_actual()
        clave = g["reto"]
        ahora = self.reloj()
        semilla = random.Random("reto|%s|%s" % (p.semilla, clave)).randrange(10 ** 6)
        spec = T.preparar_prueba(clave, self.modo, semilla, p.indicadores)
        reto = {"indice": p.ronda, "clave": clave, "nombre": T.NOMBRE_PRUEBA[clave], "semilla": semilla, "spec": spec,
                "contexto": spec["contexto"], "res": {}, "prog": {}, "estado": {}, "publico": {}}
        prep = PREPARACION_S
        if clave == "moderador":
            pubs, creadas = publicaciones_moderacion(semilla, spec["cantidad"])
            reto["pubs"] = pubs
            reto["publico"] = {"comentarios": [{"autor": x.autor, "texto": x.contenido, "creada": creadas.get(x.autor, "?")} for x in pubs],
                               "segundos_comentario": SEG_POR_COMENTARIO}
            duracion = spec["cantidad"] * SEG_POR_COMENTARIO + 6
        elif clave == "rastreador":
            duracion = spec["ajustes"]["tiempo"]
        elif clave == "contencion":
            reto["cfg"] = CW.config(self.modo, semilla)
            reto["publico"] = reto["cfg"]
            duracion = reto["cfg"]["duracion_ms"] / 1000.0
        elif clave == "plataformas":
            reto["publico"] = PL.config_cliente(spec["nivel"])
            duracion = spec["limite_s"]
        else:
            reto["chart"] = DO.cargar_chart(self.modo_duelo)
            reto["publico"] = {"modo": self.modo_duelo}
            prep = DO.PREPARACION_S
            duracion = reto["chart"]["duration_ms"] / 1000.0
        reto["inicio"] = ahora + prep
        reto["duracion"] = duracion
        reto["fin"] = reto["inicio"] + duracion + MARGEN_ENTREGA_S
        self.reto = reto
        p.fase = "reto"
        self.limite = self.siguiente_en = None
        self._tocar()

    def _en_reto(self, token, clave=None):
        self.tick()
        jid = self._jid(token)
        r = self.reto
        if self.partida.fase != "reto" or r is None or (clave and r["clave"] != clave):
            raise ErrorSala("fase", "Ese reto no está en curso.")
        return jid, r

    def _repetido_reto(self, jid, r, mid):
        """Idempotencia por reto: el mismo id en otra ronda es un mensaje distinto."""
        return self._repetido(jid, "%s|%s" % (r["indice"], mid) if mid else None)

    def _empezado(self, r):
        if self.reloj() < r["inicio"]:
            raise ErrorSala("regla", "El reto todavía no empieza.")

    def _entregado(self, jid, r, resultado):
        r["res"][jid] = resultado
        self._tocar()
        self.tick()
        return resultado

    def moderar(self, token, indice, eliminar, mid=None):
        """Una decision de Moderacion Express. Devuelve si fue correcta (el cliente no conoce la respuesta)."""
        with self.lock:
            jid, r = self._en_reto(token, "moderador")
            cola = r["estado"].setdefault(jid, ColaModeracion(r["pubs"], cuenta_regresiva=0))
            if self._repetido_reto(jid, r, mid):
                return {"repetido": True, "decididos": len(cola.historial)}
            self._empezado(r)
            if jid in r["res"] or cola.terminado():
                raise ErrorSala("regla", "Ya terminaste este reto.")
            if indice != len(cola.historial) or not isinstance(eliminar, bool):
                raise ErrorSala("regla", "Ese comentario no es el que toca.")
            actual = cola.actual
            cola.decidir(eliminar)
            _pub, _borro, correcto = cola.historial[-1]
            respuesta = {"correcto": bool(correcto), "era_bot": bool(actual.es_falsa), "decididos": len(cola.historial),
                         "racha": cola.racha, "vidas": cola.vidas, "terminado": cola.terminado()}
            if cola.terminado():
                respuesta["resultado"] = self._entregado(jid, r, self._puntuar_moderador(r, cola))
            return respuesta

    def _puntuar_moderador(self, r, cola):
        return T.puntuar_moderador(r["spec"], {"decisiones": [bool(b) for _p, b, _ok in cola.historial]})

    def _puzzle(self, jid, r):
        if jid not in r["estado"]:
            a = r["spec"]["ajustes"]
            p = PuzzleEvidencias(crear_red_civitas(), r["semilla"], eslabones=a["eslabones"], senuelos=a["senuelos"], tiempo=a["tiempo"])
            p.empezar()
            r["estado"][jid] = p
        p = r["estado"][jid]
        transcurrido = max(0.0, self.reloj() - r["inicio"])
        if p.jugando():
            p.tick(max(0.0, transcurrido + getattr(p, "gastado", 0.0) - p.transcurrido))
        return p

    def rastrear(self, token, accion, slots=None, conclusion=None, mid=None):
        """Rastreador: el tablero vive en el servidor. accion = comprobar | pista."""
        with self.lock:
            jid, r = self._en_reto(token, "rastreador")
            p = self._puzzle(jid, r)
            if self._repetido_reto(jid, r, mid):
                return self._vista_puzzle(p)
            self._empezado(r)
            if jid in r["res"]:
                raise ErrorSala("regla", "Ya terminaste este reto.")
            if accion == "pista":
                # La pista se calcula sobre el tablero que el jugador tiene AHORA en pantalla (no el ultimo comprobado).
                if isinstance(slots, list) and len(slots) == p.eslabones:
                    usados = set()
                    p.slots = [None] * p.eslabones
                    for i, carta in enumerate(slots):
                        if carta in p.cartas and carta not in usados:
                            p.slots[i] = carta
                            usados.add(carta)
                antes = p.transcurrido
                p.pedir_pista()
                p.gastado = getattr(p, "gastado", 0.0) + (p.transcurrido - antes)
            elif accion == "comprobar":
                if (not isinstance(slots, list) or len(slots) != p.eslabones or len(set(slots)) != len(slots)
                        or any(c not in p.cartas for c in slots) or conclusion not in p.opciones_conclusion):
                    raise ErrorSala("regla", "Completa la cadena y elige una conclusión.")
                p.slots = [None] * p.eslabones
                for i, carta in enumerate(slots):
                    p.colocar(carta, i)
                p.elegir_conclusion(conclusion)
                p.comprobar()
            else:
                raise ErrorSala("regla", "Acción desconocida.")
            if p.terminado():
                self._entregado(jid, r, self._puntuar_rastreador(r, p))
            return self._vista_puzzle(p, r["res"].get(jid))

    def _puntuar_rastreador(self, r, p):
        a = r["spec"]["ajustes"]
        return T.puntuar_rastreador(r["spec"], {"intentos": [[list(s), c] for s, c in p.intentos], "pistas": min(20, p.pistas_usadas),
                                                "segundos": max(2.0, min(a["tiempo"], p.transcurrido))})

    def _vista_puzzle(self, p, resultado=None):
        cartas = [{"id": c, "nombre": p.grafo.nombre(c), "hora": p.hora(c), "sigue_a": p.sigue_a(c), **p.ficha(c)} for c in p.cartas]
        return {"rumor": p.caso["viral"], "inicio": {"id": p.inicio, "nombre": p.grafo.nombre(p.inicio), "hora": p.hora(p.inicio),
                                                     "sigue_a": p.sigue_a(p.inicio), **p.ficha(p.inicio)},
                "cartas": cartas, "eslabones": p.eslabones, "opciones": [{"clave": k, "texto": CONCLUSIONES[k]} for k in p.opciones_conclusion],
                "comprobaciones": p.comprobaciones_restantes(), "restante": round(p.restante(), 1), "revision": list(p.revision),
                "conclusion_ok": p.conclusion_ok, "explicaciones": list(p.explicaciones), "estado": p.estado,
                "pista": {"nivel": p.nivel_pista, "receptor": p.pista_receptor, "candidatos": list(p.candidatos_pista), "carta": p.pista_carta},
                "pistas_usadas": p.pistas_usadas, "ultimo": {"slots": list(p.slots), "conclusion": p.conclusion}, "resultado": resultado}

    def entregar_reto(self, token, datos, mid=None):
        """Resultado de Caza-Rumores, plataformas o Duelo: el servidor lo vuelve a calcular."""
        with self.lock:
            jid, r = self._en_reto(token)
            if self._repetido_reto(jid, r, mid):
                return r["res"].get(jid)
            if r["clave"] in ("moderador", "rastreador"):
                raise ErrorSala("regla", "Este reto se juega paso a paso con el servidor.")
            if jid in r["res"]:
                raise ErrorSala("regla", "Ya entregaste este reto.")
            if not isinstance(datos, dict):
                raise ErrorSala("regla", "Resultado inválido.")
            transcurrido_ms = (self.reloj() - r["inicio"]) * 1000.0
            try:
                if r["clave"] == "contencion":
                    if transcurrido_ms < r["cfg"]["duracion_ms"] - DO.TOLERANCIA_SYNC_MS and datos.get("toques"):
                        ultimo = datos["toques"][-1][0] * CW.TICK_MS if isinstance(datos["toques"][-1], list) and datos["toques"][-1] else 0
                        if isinstance(ultimo, int) and ultimo > transcurrido_ms + DO.TOLERANCIA_SYNC_MS:
                            raise CW.ToquesInvalidos("Llegó un resultado antes de que pasara su tiempo.")
                    res = CW.puntuar(r["cfg"], datos)
                elif r["clave"] == "plataformas":
                    traza = datos.get("traza")
                    ticks = sum(s[1] for s in traza if isinstance(s, list) and len(s) == 2 and isinstance(s[1], int)) if isinstance(traza, list) else 0
                    if ticks * 1000.0 / PL.TICKS_S > transcurrido_ms + DO.TOLERANCIA_SYNC_MS + 1000:
                        raise T.ResultadoInvalido("La carrera dura más que el tiempo transcurrido.")
                    res = T.puntuar_plataformas(r["spec"], datos)
                else:
                    res = DO.validar_y_puntuar(r["chart"], datos, transcurrido_ms)
            except (T.ResultadoInvalido, CW.ToquesInvalidos) as e:
                raise ErrorSala("regla", str(e))
            return self._entregado(jid, r, res)

    def progreso(self, token, puntos=0, combo=0, avance=0.0, juzgadas=0, precision=0.0):
        """Marcador en vivo para los rivales (solo se muestra; no puntua)."""
        with self.lock:
            jid = self._jid(token)
            if self.partida.fase == "reto" and self.reto:
                self.reto["prog"][jid] = {"puntos": max(0, min(T.MAX_PRUEBA, int(puntos))), "combo": max(0, min(999, int(combo))),
                                         "avance": max(0.0, min(1.0, float(avance)))}

    def _bot_reto(self, r, jid):
        rng = random.Random("bot|%s|%s|%s" % (self.partida.semilla, r["clave"], jid))
        nivel = 0.45 + 0.4 * random.Random("nivel|%s|%s" % (self.partida.semilla, jid)).random()
        c = r["clave"]
        if c == "contencion":
            return CW.puntuar(r["cfg"], CW.toques_bot(r["cfg"], nivel, rng))
        if c == "ritmo":
            return DO.validar_y_puntuar(r["chart"], DO.payload_bot(r["chart"], nivel, rng), 10 ** 9)
        return T.puntuar(r["spec"], T.payload_bot(r["spec"], nivel, rng))

    def _cerrar_reto(self):
        p, r = self.partida, self.reto
        for jid in p.jugadores:
            if jid in r["res"]:
                continue
            if jid in self.bots:
                r["res"][jid] = self._bot_reto(r, jid)
            elif r["clave"] == "moderador" and jid in r["estado"] and r["estado"][jid].historial:
                cola = r["estado"][jid]
                while not cola.terminado():          # lo que no alcanzo a decidir cuenta como aprobado
                    cola.decidir(False)
                r["res"][jid] = self._puntuar_moderador(r, cola)
            elif r["clave"] == "rastreador" and jid in r["estado"] and r["estado"][jid].intentos:
                r["res"][jid] = self._puntuar_rastreador(r, r["estado"][jid])
            else:
                r["res"][jid] = T.no_entregado()
        for jid in p.jugadores:
            self.puntos_reto.setdefault(jid, {})[r["clave"]] = r["res"][jid]
        media, delta = T.consecuencias(r["clave"], [r["res"][jid]["normalizado"] for jid in p.jugadores])
        for k, v in delta.items():
            p.indicadores[k] = max(0, min(100, p.indicadores[k] + v))
        ganador = max(p.jugadores, key=lambda j: (r["res"][j]["normalizado"], -int(j[1:])))
        resumen = {"indice": r["indice"], "clave": r["clave"], "nombre": r["nombre"], "ganador": ganador,
                   "ganador_nombre": p.jugadores[ganador].nombre, "media": round(media * 100), "delta_ciudad": delta,
                   "resultados": dict(r["res"]), "clasificacion": self.clasificacion()}
        self.retos.append(resumen)
        self.reto = None
        p.fase = "reto_resultado"
        self.siguiente_en = self.reloj() + PAUSA_RETO_S
        self._tocar()

    def clasificacion(self):
        p = self.partida
        filas = []
        for jid, j in p.jugadores.items():
            consejo = T.puntos_consejo(j.puntos, p.total_rondas)
            pruebas = {k: v["normalizado"] for k, v in self.puntos_reto.get(jid, {}).items()}
            filas.append({"id": jid, "nombre": j.nombre, "rol": j.rol, "consejo": consejo, "pruebas": pruebas,
                          "duelo": pruebas.get("ritmo", 0), "total": consejo + sum(pruebas.values())})
        filas.sort(key=lambda f: (-f["total"], -f["duelo"], f["id"]))
        for i, f in enumerate(filas):
            f["posicion"] = i + 1
        return filas

    # ---------- ronda civica ----------
    def _abrir_ronda(self):
        evento = self._guion_actual()["evento"] if self.campana else None
        self.partida.nueva_ronda(evento)
        ahora = self.reloj()
        self.limite = ahora + self.partida.tiempo_ronda()
        self.restante_pausa = self.siguiente_en = None
        for jid, datos in self.bots.items():
            datos[1] = ahora + datos[0].uniform(2.0, min(8.0, self.partida.tiempo_ronda() - 2))
        self._tocar()

    def accion(self, token, ronda, ruta, mid=None):
        with self.lock:
            self.tick()
            jid = self._jid(token)
            if self._repetido(jid, mid):
                return
            if self.partida.fase != "ronda" or ronda != self.partida.ronda:
                raise ErrorSala("ronda", "Esa acción es de otra ronda.")
            if self.restante_pausa is not None:
                raise ErrorSala("pausa", "La partida está en pausa.")
            if not isinstance(ruta, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ruta):
                raise ErrorSala("ruta", "Ruta inválida.")
            error = self.partida.registrar_accion(jid, ruta)
            if error:
                raise ErrorSala("regla", error)
            self._tocar()
            if self.partida.todos_decidieron():
                self._cerrar_ronda()

    def pausa(self, token, pausar):
        with self.lock:
            self._anfitrion(token, "pausar")
            if self.partida.fase == "reto":
                raise ErrorSala("fase", "Un reto no se puede pausar: todos compiten a la vez.")
            if self.partida.fase != "ronda":
                raise ErrorSala("fase", "Solo se puede pausar durante una ronda.")
            ahora = self.reloj()
            if pausar and self.restante_pausa is None:
                self.restante_pausa = max(0.0, self.limite - ahora)
            elif not pausar and self.restante_pausa is not None:
                self.limite = ahora + self.restante_pausa
                self.restante_pausa = None
            self._tocar()

    def continuar(self, token):
        with self.lock:
            self._anfitrion(token, "continuar")
            if self.partida.fase in ("resultado", "reto_resultado"):
                self.siguiente_en = self.reloj()
                self.tick()

    def _cerrar_ronda(self):
        self.partida.resolver_ronda()
        self.limite = None
        self.siguiente_en = self.reloj() + PAUSA_RESULTADO_S
        self._tocar()

    def tick(self):
        """Avanza el reloj de la sala: presencia, bots, escenas, retos, fin de ronda por tiempo y paso de ronda."""
        with self.lock:
            ahora = self.reloj()
            p = self.partida
            for jid, j in p.jugadores.items():
                if jid not in self.bots:
                    conectado = ahora - self.visto.get(jid, ahora) <= PRESENCIA_S
                    if j.conectado != conectado:
                        j.conectado = conectado
                        self._tocar()
            if p.fase == "escena":
                humanos = self._humanos()
                if ahora >= self.escena_fin or (humanos and all(h in self.escena_listos for h in humanos)):
                    self._abrir_reto()
            elif p.fase == "reto":
                r = self.reto
                humanos = self._humanos()
                if ahora >= r["fin"] or (ahora >= r["inicio"] and all(h in r["res"] for h in humanos)):
                    self._cerrar_reto()
            elif p.fase == "reto_resultado" and self.siguiente_en is not None and ahora >= self.siguiente_en:
                self._abrir_ronda()
            elif p.fase == "ronda" and self.restante_pausa is None:
                for jid, (rng, cuando) in self.bots.items():
                    if jid not in p.acciones and cuando is not None and ahora >= cuando:
                        p.registrar_accion(jid, elegir_ruta(p.arbol_de(jid), "responsable", rng))
                        self._tocar()
                if (self.limite is not None and ahora >= self.limite) or p.todos_decidieron():
                    self._cerrar_ronda()
            elif p.fase == "resultado" and self.siguiente_en is not None and ahora >= self.siguiente_en:
                if p.cerrar_resultado() is None:
                    self._siguiente_ronda()
                else:
                    self._tocar()
            if p.fase == "final" and self.campana and not self.torneo_final:
                self._final_torneo()

    def _final_torneo(self):
        p = self.partida
        tabla = self.clasificacion()
        for h in self.retos:
            if h["delta_ciudad"]:
                p.eleccion["explicacion"].append("%s: la media del grupo fue %d/100, así que %s." % (
                    h["nombre"], h["media"], ", ".join("%s %+d" % (NOMBRE_INDICADOR[k].lower(), v) for k, v in h["delta_ciudad"].items())))
        duelo = next((h for h in self.retos if h["clave"] == "ritmo"), None)
        p.eleccion["torneo"] = {"campeon": tabla[0]["id"], "campeon_nombre": tabla[0]["nombre"], "clasificacion": tabla,
                                "duelo_ganador": duelo["ganador_nombre"] if duelo else None,
                                "pruebas": [{"clave": h["clave"], "nombre": h["nombre"], "ganador_nombre": h["ganador_nombre"]} for h in self.retos],
                                "mensaje": T.mensaje_final(tabla[0], p.eleccion["ciudad"])}
        self.torneo_final = True
        self._tocar()

    # ---------- vistas ----------
    def _comun(self):
        p = self.partida
        datos = p.estado_publico()
        restante = None
        if self.restante_pausa is not None:
            restante = self.restante_pausa
        elif p.fase == "ronda" and self.limite is not None:
            restante = max(0.0, self.limite - self.reloj())
        datos.update(codigo=self.codigo, anfitrion=self.anfitrion, listos=sorted(self.listos), pausado=self.restante_pausa is not None,
                     restante=None if restante is None else round(restante, 1), version=self.version, bots=sorted(self.bots),
                     campana=self.campana, modo=self.modo)
        if self.campana:
            datos["clasificacion"] = self.clasificacion()
            datos["plan"] = [{"reto": g["reto"], "nombre": T.NOMBRE_PRUEBA[g["reto"]], "titulo": g["titulo"]} for g in self.guion]
            datos["duelo_modo"] = self.modo_duelo
            if p.fase not in ("lobby", "final"):
                datos["titulo_ronda"] = self._guion_actual()["titulo"]
                datos["ronda_campana"] = self.idx + 1
        if p.fase in ("reto_resultado", "final") and self.retos:
            datos["reto_resumen"] = self.retos[-1]
        return datos

    def vista(self, token, con_grafo=False):
        with self.lock:
            self.tick()
            jid = self._jid(token)
            p = self.partida
            datos = self._comun()
            datos["yo"] = jid
            ahora = self.reloj()
            if p.fase == "escena":
                roles = {j.rol for j in p.jugadores.values()}
                datos["escena"] = CA.escena(self._guion_actual(), p.jugadores[jid].rol, roles)      # SOLO la pista de su rol
                datos["escena"].update(ronda=p.ronda + 1, total=p.total_rondas, restante=round(max(0.0, self.escena_fin - ahora), 1),
                                       listo=jid in self.escena_listos, listos=sorted(self.escena_listos))
            if p.fase == "reto" and self.reto:
                r = self.reto
                datos["reto"] = {"indice": r["indice"], "clave": r["clave"], "nombre": r["nombre"], "contexto": r["contexto"],
                                 "intro": self._guion_actual()["reto_intro"], "inicio_en_ms": round((r["inicio"] - ahora) * 1000),
                                 "fin_en_ms": round((r["fin"] - ahora) * 1000), "duracion_ms": round(r["duracion"] * 1000),
                                 "ya_entregaste": jid in r["res"], "mi_resultado": r["res"].get(jid), "entregaron": sorted(r["res"]),
                                 "progreso": r["prog"], "config": r["publico"]}
                if r["clave"] == "moderador":
                    cola = r["estado"].get(jid)
                    datos["reto"]["decididos"] = len(cola.historial) if cola else 0
                elif r["clave"] == "rastreador":
                    datos["reto"]["tablero"] = self._vista_puzzle(self._puzzle(jid, r), r["res"].get(jid))
            if p.fase == "ronda":
                datos["ronda_info"] = p.vista_ronda_publica()
                datos["arbol"] = p.arbol_de(jid)
                datos["ya_decidiste"] = jid in p.acciones
                if self.campana:
                    datos["decision_intro"] = self._guion_actual()["decision_intro"]
            if p.fase in ("resultado", "final") and p.ultimo_resultado:
                datos["resultado"] = p.ultimo_resultado
            if p.fase == "final":
                datos["final"] = p.eleccion
            if con_grafo:
                datos["grafo"] = p.grafo_publico()
            return datos

    def vista_publica(self):
        """Pantalla de espectadores (stand de la feria): estado y clasificacion, sin pistas de rol ni arboles."""
        with self.lock:
            self.tick()
            datos = self._comun()
            p = self.partida
            if p.fase == "reto" and self.reto:
                r = self.reto
                datos["reto"] = {"clave": r["clave"], "nombre": r["nombre"], "entregaron": sorted(r["res"]), "progreso": r["prog"],
                                 "inicio_en_ms": round((r["inicio"] - self.reloj()) * 1000)}
            if p.fase == "final":
                datos["final"] = p.eleccion
            return datos
