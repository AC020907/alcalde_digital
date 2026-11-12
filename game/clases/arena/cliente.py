"""
Cliente de la Arena Civitas. Lo usan la interfaz de Ren'Py y los bots de prueba.

Un hilo lee del socket y deja los mensajes en una cola; quien dibuja llama a procesar() desde su propio
hilo, asi el estado solo cambia en un lugar. El cliente nunca calcula puntos ni resultados: muestra lo
que manda el servidor.
"""
import queue
import socket
import threading
import time
import uuid

from clases.arena import protocolo


class ClienteArena(object):
    def __init__(self, host, puerto=protocolo.PUERTO, timeout=4.0):
        self.host, self.puerto, self.timeout = host, puerto, timeout
        self.sock = None
        self.cola = queue.Queue()
        self.vivo = False
        self.lock = threading.Lock()
        self.ultimo_seq = 0
        # Vista agregada (lo que muestra la interfaz)
        self.jugador_id = None
        self.token = None
        self.anfitrion = None
        self.grafo = None
        self.estado = None
        self.ronda = None
        self.arbol = None
        self.resultado = None
        self.final = None
        self.prueba = None            # spec de la prueba del torneo en curso
        self.mi_resultado = None
        self.resumen = None
        self.error = None
        self.cerrado = None
        self.restante_hasta = None    # instante local en que vence la ronda segun el servidor
        self.pendientes = {}          # id -> mensaje sin ack (para reenviar tras reconectar)

    # ---------- conexion ----------
    def conectar(self):
        self.sock = socket.create_connection((self.host, self.puerto), timeout=self.timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.settimeout(1.0)
        self.vivo = True
        self.cerrado = None
        threading.Thread(target=self._leer, daemon=True).start()

    def cerrar(self):
        if self.vivo:
            try:
                self.enviar("salir")
            except OSError:
                pass
        self.vivo = False
        try:
            self.sock.close()
        except (OSError, AttributeError):
            pass

    def _leer(self):
        buf = b""
        while self.vivo:
            try:
                datos = self.sock.recv(65536)
            except socket.timeout:
                continue
            except OSError:
                break
            if not datos:
                break
            buf += datos
            while b"\n" in buf:
                linea, buf = buf.split(b"\n", 1)
                try:
                    self.cola.put(protocolo.decodificar(linea))
                except protocolo.ErrorProtocolo:
                    continue
        self.vivo = False
        self.cola.put({"tipo": "_desconectado"})

    def enviar(self, tipo, **datos):
        mensaje = dict(datos, tipo=tipo, id=uuid.uuid4().hex[:16])
        if tipo in ("accion", "resultado_prueba"):
            self.pendientes[mensaje["id"]] = mensaje
        with self.lock:
            self.sock.sendall(protocolo.codificar(mensaje))
        return mensaje["id"]

    # ---------- acciones del jugador ----------
    def unirse(self, nombre, rol, token=None, clave=None):
        return self.enviar("hola", nombre=nombre, rol=rol, token=token, clave=clave)

    def reconectar(self):
        """Nueva conexion con el mismo token: el servidor devuelve el mismo puesto y la ronda en curso."""
        self.conectar()
        self.unirse("", "", self.token)
        for mensaje in list(self.pendientes.values()):
            with self.lock:
                self.sock.sendall(protocolo.codificar(mensaje))   # mismo id: el servidor no lo duplica

    def decidir(self, ruta):
        if not self.ronda:
            return None
        return self.enviar("accion", ronda=self.ronda["ronda"], ruta=list(ruta))

    def entregar_prueba(self, datos):
        if not self.prueba:
            return None
        return self.enviar("resultado_prueba", indice=self.prueba["indice"], datos=datos)

    # ---------- procesamiento ----------
    def procesar(self):
        """Aplica los mensajes recibidos. Devuelve la lista procesada (para registro o pruebas)."""
        vistos = []
        while True:
            try:
                msg = self.cola.get_nowait()
            except queue.Empty:
                return vistos
            seq = msg.get("seq")
            if seq is not None:
                if seq <= self.ultimo_seq:
                    continue
                self.ultimo_seq = seq
            self._aplicar(msg)
            vistos.append(msg)

    def esperar(self, condicion, segundos=10.0):
        """Para pruebas y bots: procesa hasta que condicion(self) sea verdadera."""
        fin = time.monotonic() + segundos
        while time.monotonic() < fin:
            self.procesar()
            if condicion(self):
                return True
            time.sleep(0.02)
        self.procesar()
        return condicion(self)

    def _aplicar(self, msg):
        tipo = msg.get("tipo")
        if tipo == "bienvenida":
            self.jugador_id, self.token = msg["jugador_id"], msg["token"]
            self.anfitrion, self.grafo = msg["anfitrion"], msg["grafo"]
            self.error = None
        elif tipo == "grafo":
            self.grafo = msg["grafo"]
        elif tipo == "estado":
            self.estado = msg["estado"]
            self.anfitrion = self.estado.get("anfitrion")
            if self.estado.get("restante") is not None:
                self.restante_hasta = time.monotonic() + self.estado["restante"]
        elif tipo == "ronda":
            self.error = None   # un aviso del lobby ya no aplica cuando la partida empezo
            self.ronda, self.arbol = msg, msg["arbol"]
            self.resultado = None
            self.restante_hasta = time.monotonic() + msg["segundos"]
        elif tipo == "resultado":
            self.resultado = msg["resultado"]
            self.ronda, self.arbol = None, None
            self.pendientes.clear()
        elif tipo == "prueba":
            self.prueba, self.resumen, self.ronda, self.arbol, self.resultado = msg["spec"], None, None, None, None
            if not msg.get("ya_entregaste"):
                self.mi_resultado = None
            if msg.get("limite") is not None:
                self.restante_hasta = time.monotonic() + msg["limite"]
        elif tipo == "mi_resultado":
            self.mi_resultado = msg["resultado"]
            self.pendientes.clear()
        elif tipo == "resumen_prueba":
            self.resumen, self.prueba = msg["resumen"], None
            self.pendientes.clear()
        elif tipo == "final":
            self.final = msg["final"]
            self.prueba = None
        elif tipo == "ack":
            self.pendientes.pop(msg.get("ref"), None)
        elif tipo == "error":
            self.error = msg.get("mensaje")
            self.pendientes.pop(msg.get("ref"), None)
        elif tipo == "cierre":
            self.cerrado = msg.get("mensaje", "El servidor se cerró.")
        elif tipo == "_desconectado" and not self.cerrado:   # no tapar el motivo que dio el servidor
            self.cerrado = "Se perdió la conexión con el servidor."

    # ---------- consultas para la interfaz ----------
    def restante(self):
        if self.estado and self.estado.get("pausado"):
            return self.estado.get("restante") or 0
        if self.restante_hasta is None or (self.ronda is None and self.prueba is None):
            return None
        return max(0.0, self.restante_hasta - time.monotonic())

    def soy_anfitrion(self):
        return self.jugador_id is not None and self.jugador_id == self.anfitrion

    def ya_decidi(self):
        return bool(self.estado and self.jugador_id in self.estado.get("decidieron", ()))
