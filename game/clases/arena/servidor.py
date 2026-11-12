"""
Servidor autoritativo de la Arena Civitas (TCP, un hilo por cliente + un hilo de reloj).

El servidor es la unica fuente de verdad: guarda la Partida (reglas.py), controla el tiempo de cada
ronda, valida cada accion contra el arbol del jugador y calcula propagacion, indicadores, puntuaciones y
eleccion. Los clientes solo envian lo que el jugador eligio; nunca puntos ni resultados.

Uso independiente (LAN, sin internet):
    python servidor_arena.py --puerto 50777 --rondas 5 --segundos 25
"""
import socket
import threading
import time
import uuid

from clases.arena import protocolo
from clases.arena.reglas import Partida, MIN_JUGADORES
from clases.arena.torneo import TorneoArena, ResultadoInvalido, limite_segundos, MODOS_TORNEO

MAX_MALFORMADOS = 5


class Sesion(object):
    def __init__(self, sock, direccion):
        self.sock = sock
        self.direccion = direccion
        self.jid = None
        self.lock = threading.Lock()
        self.vivo = True
        self.malformados = 0

    def enviar(self, mensaje):
        try:
            with self.lock:
                self.sock.sendall(protocolo.codificar(mensaje))
            return True
        except OSError:
            self.vivo = False
            return False


class ServidorArena(object):
    def __init__(self, host="0.0.0.0", puerto=protocolo.PUERTO, semilla=None, rondas=5, segundos=25,
                 pausa_resultado=8.0, reloj=time.monotonic, clave_anfitrion=None, torneo=None,
                 pausa_resumen=12.0, escala_limite=1.0):
        self.host, self.puerto = host, puerto
        self.semilla = semilla if semilla is not None else int(time.time())
        self.rondas, self.segundos = rondas, segundos
        self.pausa_resultado = pausa_resultado
        self.reloj = reloj
        # Quien crea la sala desde el juego conoce esta clave y queda como anfitrion aunque otro llegue antes.
        # Sin clave (servidor dedicado), el anfitrion es el primero en unirse.
        self.clave_anfitrion = clave_anfitrion
        self.lock = threading.RLock()
        if torneo and rondas is None:
            rondas = MODOS_TORNEO[torneo]["rondas_civicas"]
        self.partida = Partida(self.semilla, rondas or 5, segundos)
        # Torneo: Consejo Civico -> 5 pruebas con los minijuegos -> eleccion. Sin torneo, la Arena clasica.
        self.torneo = TorneoArena(self.partida, torneo) if torneo else None
        self.partida.con_torneo = bool(torneo)
        self.pausa_resumen = pausa_resumen
        self.escala_limite = escala_limite   # las pruebas automaticas acortan la espera maxima
        self.sesiones = []
        self.tokens = {}              # token -> jid
        self.listos = set()
        self.anfitrion = None
        self.ids_vistos = {}          # jid -> set(id de mensaje)
        self.seq = 0
        self.limite = None            # instante en que cierra la ronda
        self.restante_pausa = None    # segundos que quedaban al pausar
        self.siguiente_en = None      # instante en que empieza la siguiente ronda
        self.activo = False
        self.sock = None
        self.registro = []            # eventos para depurar y para las pruebas

    # ---------- ciclo de vida ----------
    def iniciar(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.puerto))
        self.puerto = self.sock.getsockname()[1]
        self.sock.listen(8)
        self.sock.settimeout(0.5)
        self.activo = True
        for destino in (self._aceptar, self._reloj):
            threading.Thread(target=destino, daemon=True).start()
        return self.puerto

    def detener(self):
        self.activo = False
        with self.lock:
            for s in self.sesiones:
                s.enviar({"tipo": "cierre", "mensaje": "El servidor se cerró."})
                try:
                    s.sock.close()
                except OSError:
                    pass
        try:
            self.sock.close()
        except (OSError, AttributeError):
            pass

    def _aceptar(self):
        while self.activo:
            try:
                conn, direccion = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sesion = Sesion(conn, direccion)
            with self.lock:
                self.sesiones.append(sesion)
            threading.Thread(target=self._leer, args=(sesion,), daemon=True).start()

    def _leer(self, sesion):
        buf = b""
        sesion.sock.settimeout(1.0)
        while self.activo and sesion.vivo:
            try:
                datos = sesion.sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not datos:
                break
            buf += datos
            if len(buf) > protocolo.MAX_LINEA and b"\n" not in buf:
                sesion.enviar({"tipo": "error", "codigo": "muy_largo", "mensaje": "Mensaje demasiado largo."})
                break
            while b"\n" in buf:
                linea, buf = buf.split(b"\n", 1)
                if linea.strip():
                    self._procesar_linea(sesion, linea)
        self._desconectar(sesion)

    # ---------- mensajes ----------
    def _procesar_linea(self, sesion, linea):
        try:
            msg = protocolo.validar_cliente(protocolo.decodificar(linea))
        except protocolo.ErrorProtocolo as e:
            sesion.malformados += 1
            sesion.enviar({"tipo": "error", "codigo": e.codigo, "mensaje": e.mensaje})
            if sesion.malformados >= MAX_MALFORMADOS:
                sesion.vivo = False
            return
        with self.lock:
            if sesion.jid is not None:
                vistos = self.ids_vistos.setdefault(sesion.jid, set())
                if msg["id"] in vistos:
                    sesion.enviar({"tipo": "ack", "ref": msg["id"], "repetido": True})
                    return
                vistos.add(msg["id"])
            manejador = getattr(self, "_m_" + msg["tipo"])
            error = manejador(sesion, msg)
            if error:
                sesion.enviar({"tipo": "error", "codigo": "regla", "mensaje": error, "ref": msg["id"]})
            else:
                sesion.enviar({"tipo": "ack", "ref": msg["id"]})

    def _m_hola(self, sesion, msg):
        token = msg.get("token")
        if token and token in self.tokens:
            jid = self.tokens[token]
            for otra in self.sesiones:
                if otra is not sesion and otra.jid == jid:
                    otra.jid = None
                    otra.vivo = False
            sesion.jid = jid
            self.partida.jugadores[jid].conectado = True
            self._log("reconexion", jid)
            sesion.enviar(self._bienvenida(jid, token))
            self._reenviar_ronda(sesion)
            self._difundir_estado()
            return None
        if sesion.jid is not None:
            return "Ya estás en la sala."
        jid = "j%d" % (len(self.tokens) + 1)
        error = self.partida.unir(jid, msg["nombre"], msg["rol"])
        if error:
            return error
        token = uuid.uuid4().hex
        self.tokens[token] = jid
        sesion.jid = jid
        if self.clave_anfitrion and msg.get("clave") == self.clave_anfitrion:
            self.anfitrion = jid
        elif self.anfitrion is None:
            self.anfitrion = jid
        self._log("union", jid, msg["rol"])
        sesion.enviar(self._bienvenida(jid, token))
        self._difundir_estado()
        return None

    def _bienvenida(self, jid, token):
        return {"tipo": "bienvenida", "jugador_id": jid, "token": token, "anfitrion": self.anfitrion,
                "grafo": self.partida.grafo_publico(), "semilla": self.semilla}

    def _m_listo(self, sesion, msg):
        if sesion.jid is None:
            return "Primero únete a la sala."
        if msg["listo"]:
            self.listos.add(sesion.jid)
        else:
            self.listos.discard(sesion.jid)
        self._difundir_estado()
        return None

    def _m_empezar(self, sesion, msg):
        if sesion.jid != self.anfitrion:
            return "Solo el anfitrión puede empezar."
        if not self.partida.puede_empezar():
            return "Se necesitan de %d a 4 jugadores." % MIN_JUGADORES
        if set(self.partida.jugadores) - self.listos - {self.anfitrion}:
            return "Faltan jugadores por marcar 'Listo'."
        self._log("inicio", sesion.jid, len(self.partida.jugadores))
        self._abrir_ronda()
        return None

    def _m_accion(self, sesion, msg):
        if sesion.jid is None:
            return "Primero únete a la sala."
        if msg["ronda"] != self.partida.ronda:
            return "Esa acción es de otra ronda."
        if self.restante_pausa is not None:
            return "La partida está en pausa."
        error = self.partida.registrar_accion(sesion.jid, msg["ruta"])
        if error:
            return error
        self._log("accion", sesion.jid, self.partida.ronda)
        self._difundir_estado()
        if self.partida.todos_decidieron():
            self._cerrar_ronda()
        return None

    def _m_pausa(self, sesion, msg):
        if sesion.jid != self.anfitrion:
            return "Solo el anfitrión puede pausar."
        if self.partida.fase != "ronda":
            return "Solo se puede pausar durante una ronda."
        ahora = self.reloj()
        if msg["pausar"] and self.restante_pausa is None:
            self.restante_pausa = max(0.0, self.limite - ahora)
        elif not msg["pausar"] and self.restante_pausa is not None:
            self.limite = ahora + self.restante_pausa
            self.restante_pausa = None
        self._difundir_estado()
        return None

    def _m_continuar(self, sesion, msg):
        if sesion.jid != self.anfitrion:
            return "Solo el anfitrión puede continuar."
        if self.partida.fase not in ("resultado", "resumen"):
            return "No hay un resultado que cerrar."
        self.siguiente_en = self.reloj()
        return None

    def _m_resultado_prueba(self, sesion, msg):
        if sesion.jid is None:
            return "Primero únete a la sala."
        if self.torneo is None or self.partida.fase != "prueba":
            return "No hay ninguna prueba abierta."
        if msg["indice"] != self.torneo.indice:
            return "Ese resultado es de otra prueba."
        try:
            puntuado = self.torneo.entregar(sesion.jid, msg["datos"])
        except ResultadoInvalido as e:
            self._log("resultado_invalido", sesion.jid, str(e))
            return str(e)
        self._log("entrega", sesion.jid, self.torneo.spec["clave"], puntuado["normalizado"])
        sesion.enviar({"tipo": "mi_resultado", "seq": self._seq(), "indice": self.torneo.indice, "resultado": puntuado})
        self._difundir_estado()
        if self.torneo.todos_entregaron():
            self._cerrar_prueba()
        return None

    def _m_salir(self, sesion, msg):
        sesion.vivo = False
        return None

    def _m_ping(self, sesion, msg):
        return None

    # ---------- rondas ----------
    def _abrir_ronda(self):
        if self.partida.ronda == 0:
            # Al empezar, todos reciben la red social completa (ya con las cuentas de todos los jugadores).
            self._difundir({"tipo": "grafo", "grafo": self.partida.grafo_publico()})
        vista = self.partida.nueva_ronda()
        self.limite = self.reloj() + self.partida.tiempo_ronda()
        self.restante_pausa = None
        self.siguiente_en = None
        for s in self.sesiones:
            self._reenviar_ronda(s, vista)
        self._difundir_estado()

    def _reenviar_ronda(self, sesion, vista=None):
        if self.partida.fase == "ronda" and sesion.jid in self.partida.jugadores:
            vista = vista or self.partida.vista_ronda_publica()
            sesion.enviar(dict(tipo="ronda", seq=self._seq(), arbol=self.partida.arbol_de(sesion.jid),
                               ya_decidiste=sesion.jid in self.partida.acciones, **vista))
        elif self.partida.fase == "resultado" and self.partida.ultimo_resultado:
            sesion.enviar({"tipo": "resultado", "seq": self._seq(), "resultado": self.partida.ultimo_resultado})
        elif self.partida.fase == "prueba" and self.torneo.spec:
            sesion.enviar(dict(tipo="prueba", seq=self._seq(), spec=self.torneo.spec, limite=self._restante(),
                               ya_entregaste=sesion.jid in self.torneo.entregas))
        elif self.partida.fase == "resumen" and self.torneo.historial:
            sesion.enviar({"tipo": "resumen_prueba", "seq": self._seq(), "resumen": self.torneo.historial[-1]})
        elif self.partida.fase == "final":
            sesion.enviar({"tipo": "final", "seq": self._seq(), "final": self.partida.eleccion})

    def _cerrar_ronda(self):
        resultado = self.partida.resolver_ronda()
        self._log("resultado", self.partida.ronda, resultado["n_alcanzados"])
        self.limite = None
        self.siguiente_en = self.reloj() + self.pausa_resultado
        self._difundir({"tipo": "resultado", "resultado": resultado})
        self._difundir_estado()

    def _reloj(self):
        while self.activo:
            time.sleep(0.1)
            with self.lock:
                ahora = self.reloj()
                fase = self.partida.fase
                if fase == "ronda" and self.restante_pausa is None and self.limite is not None and ahora >= self.limite:
                    self._log("tiempo_agotado", self.partida.ronda)
                    self._cerrar_ronda()
                elif fase == "resultado" and self.siguiente_en is not None and ahora >= self.siguiente_en:
                    final = self.partida.cerrar_resultado()
                    if self.torneo and self.partida.consejo_terminado():
                        self._abrir_prueba()
                    elif final:
                        self._log("final", final["ganador"])
                        self._difundir({"tipo": "final", "final": final})
                        self._difundir_estado()
                    else:
                        self._abrir_ronda()
                elif fase == "prueba" and self.limite is not None and ahora >= self.limite:
                    self._log("prueba_tiempo_agotado", self.torneo.indice)
                    self._cerrar_prueba()
                elif fase == "resumen" and self.siguiente_en is not None and ahora >= self.siguiente_en:
                    self._abrir_prueba()

    # ---------- torneo de minijuegos ----------
    def _abrir_prueba(self):
        spec = self.torneo.abrir_siguiente()
        if spec is None:
            final = self.torneo.final()
            self.partida.eleccion = final
            self._log("final", final["ganador"], final["torneo"]["campeon"])
            self._difundir({"tipo": "final", "final": final})
            self._difundir_estado()
            return
        self.partida.fase = "prueba"
        self.limite = self.reloj() + limite_segundos(spec) * self.escala_limite
        self.siguiente_en = None
        self._log("prueba", spec["clave"], spec["semilla"])
        self._difundir({"tipo": "prueba", "spec": spec, "limite": self._restante(), "ya_entregaste": False})
        self._difundir_estado()

    def _cerrar_prueba(self):
        resumen = self.torneo.cerrar_prueba()
        self.partida.fase = "resumen"
        self.limite = None
        self.siguiente_en = self.reloj() + self.pausa_resumen
        self._log("resumen", resumen["clave"], resumen["ganador"])
        self._difundir({"tipo": "resumen_prueba", "resumen": resumen})
        self._difundir_estado()

    # ---------- conexion ----------
    def _desconectar(self, sesion):
        with self.lock:
            if sesion in self.sesiones:
                self.sesiones.remove(sesion)
            try:
                sesion.sock.close()
            except OSError:
                pass
            jid = sesion.jid
            if jid is None or any(s.jid == jid for s in self.sesiones):
                return
            self._log("desconexion", jid)
            if self.partida.fase == "lobby":
                self.partida.quitar(jid)
                self.listos.discard(jid)
                for token in [t for t, j in self.tokens.items() if j == jid]:
                    del self.tokens[token]
                if self.anfitrion == jid:
                    self.anfitrion = next(iter(self.partida.jugadores), None)
            elif jid in self.partida.jugadores:
                # En juego conserva su puesto: si vuelve con su token, sigue; mientras, cuenta como sin respuesta.
                self.partida.jugadores[jid].conectado = False
                if self.partida.fase == "ronda" and self.partida.todos_decidieron():
                    self._cerrar_ronda()
                elif self.partida.fase == "prueba" and self.torneo.todos_entregaron():
                    self._cerrar_prueba()
            self._difundir_estado()

    # ---------- difusion ----------
    def _seq(self):
        self.seq += 1
        return self.seq

    def _difundir(self, mensaje):
        for s in list(self.sesiones):
            if s.jid is not None:
                s.enviar(dict(mensaje, seq=self._seq()))

    def _difundir_estado(self):
        estado = self.partida.estado_publico()
        estado.update(anfitrion=self.anfitrion, listos=sorted(self.listos), pausado=self.restante_pausa is not None,
                      restante=self._restante(), semilla=self.semilla,
                      modo_torneo=self.torneo.modo if self.torneo else None)
        if self.torneo:
            estado.update(prueba=self.torneo.indice, entregaron=sorted(self.torneo.entregas),
                          clasificacion=self.torneo.clasificacion() if self.torneo.historial else None)
        self._difundir({"tipo": "estado", "estado": estado})

    def _restante(self):
        if self.restante_pausa is not None:
            return round(self.restante_pausa, 1)
        if self.partida.fase in ("ronda", "prueba") and self.limite is not None:
            return round(max(0.0, self.limite - self.reloj()), 1)
        return None

    def _log(self, *evento):
        self.registro.append(evento)

    def direcciones_lan(self):
        """IPs de este equipo para que los demas se unan (se muestran en la sala)."""
        ips = set()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.255.255.255", 1))   # no envia nada: solo elige la interfaz de salida
            ips.add(s.getsockname()[0])
            s.close()
        except OSError:
            pass
        try:
            ips.update(i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
        except OSError:
            pass
        ips.discard("127.0.0.1")
        return sorted(ips) or ["127.0.0.1"]
