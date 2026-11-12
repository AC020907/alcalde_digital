"""
Arena Civitas en red: servidor real (sockets TCP en 127.0.0.1) con 2, 3 y 4 clientes reales.
- Clientes en hilos (rapido) y clientes como PROCESOS independientes (tests/arena_bot.py).
- Sincronizacion: todos ven el mismo estado final; acciones simultaneas; tiempo agotado; mensajes
  malformados; ids repetidos; puntos enviados por el cliente que se ignoran; desconexion y reconexion.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "game"))

from clases.arena import protocolo  # noqa: E402
from clases.arena.cliente import ClienteArena  # noqa: E402
from clases.arena.reglas import ROLES  # noqa: E402
from clases.arena.servidor import ServidorArena  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arena_bot import elegir_ruta  # noqa: E402


def servidor(**kw):
    s = ServidorArena(host="127.0.0.1", puerto=0, semilla=kw.pop("semilla", 42), rondas=kw.pop("rondas", 3),
                      segundos=kw.pop("segundos", 8), pausa_resultado=kw.pop("pausa_resultado", 0.3), **kw)
    s.iniciar()
    return s


def unir(s, rol, nombre=None):
    c = ClienteArena("127.0.0.1", s.puerto)
    c.conectar()
    c.unirse(nombre or rol, rol)
    assert c.esperar(lambda c: c.jugador_id or c.error, 5), "sin respuesta"
    return c


def jugar_hasta_final(clientes, politica="responsable", limite=60):
    import random
    rng = random.Random(0)
    fin = time.monotonic() + limite
    hechas = {id(c): set() for c in clientes}
    while time.monotonic() < fin:
        for c in clientes:
            c.procesar()
            if c.ronda and c.arbol and c.ronda["ronda"] not in hechas[id(c)]:
                hechas[id(c)].add(c.ronda["ronda"])
                c.decidir(elegir_ruta(c.arbol, politica, rng))
        if all(c.final for c in clientes):
            return True
        time.sleep(0.01)
    return False


class TestArenaRed(unittest.TestCase):
    def tearDown(self):
        for c in getattr(self, "clientes", []):
            c.cerrar()
        if getattr(self, "srv", None):
            self.srv.detener()

    def partida_con(self, n, **kw):
        self.srv = servidor(**kw)
        self.clientes = [unir(self.srv, rol) for rol in ROLES[:n]]
        for c in self.clientes[1:]:
            c.enviar("listo", listo=True)
        anfitrion = self.clientes[0]
        self.assertTrue(anfitrion.soy_anfitrion())
        anfitrion.esperar(lambda c: c.estado and len(c.estado["listos"]) == n - 1, 5)
        anfitrion.enviar("empezar")
        for c in self.clientes:
            assert c.esperar(lambda c: c.arbol is not None, 5), "la ronda no llego a todos"
        return self.clientes

    def test_2_3_y_4_jugadores_llegan_al_mismo_final(self):
        for n in (2, 3, 4):
            with self.subTest(jugadores=n):
                clientes = self.partida_con(n, semilla=100 + n)
                self.assertTrue(jugar_hasta_final(clientes))
                finales = [json.dumps(c.final, sort_keys=True) for c in clientes]
                self.assertEqual(len(set(finales)), 1, "los clientes divergen")
                for c in clientes:
                    c.esperar(lambda c: c.estado and c.estado["fase"] == "final", 3)
                indicadores = {json.dumps(c.estado["indicadores"], sort_keys=True) for c in clientes}
                self.assertEqual(len(indicadores), 1)
                self.assertEqual(len(clientes[0].final["ranking"]), n)
                for c in clientes:   # todos tienen la red completa, con las cuentas de todos los jugadores
                    nodos = {x["id"] for x in c.grafo["nodos"]}
                    self.assertTrue(all("j:" + o.jugador_id in nodos for o in clientes))
                self.tearDown()

    def test_quien_crea_la_sala_es_anfitrion_aunque_llegue_despues(self):
        self.srv = servidor(clave_anfitrion="secreta")
        otro = unir(self.srv, "periodista")
        dueno = ClienteArena("127.0.0.1", self.srv.puerto)
        dueno.conectar()
        dueno.unirse("Ana", "ciudadano", clave="secreta")
        self.clientes = [otro, dueno]
        dueno.esperar(lambda c: c.jugador_id and c.estado and c.estado["anfitrion"] == c.jugador_id, 5)
        self.assertTrue(dueno.soy_anfitrion())
        otro.esperar(lambda c: c.estado and c.estado["anfitrion"] == dueno.jugador_id, 5)
        self.assertFalse(otro.soy_anfitrion())

    def test_roles_duplicados_y_sala_llena(self):
        self.srv = servidor()
        self.clientes = [unir(self.srv, "periodista")]
        dup = unir(self.srv, "periodista")
        self.clientes.append(dup)
        self.assertIn("ocupado", dup.error)
        self.assertIsNone(dup.jugador_id)
        for rol in ("ciudadano", "influencer", "candidato"):
            self.clientes.append(unir(self.srv, rol))
        self.assertEqual(len(self.srv.partida.jugadores), 4)

    def test_no_empieza_con_un_jugador_ni_sin_listos_ni_si_no_eres_anfitrion(self):
        self.srv = servidor()
        a = unir(self.srv, "ciudadano")
        self.clientes = [a]
        a.enviar("empezar")
        a.esperar(lambda c: c.error, 3)
        self.assertIn("2 a 4", a.error)
        b = unir(self.srv, "periodista")
        self.clientes.append(b)
        a.error = None
        a.enviar("empezar")
        a.esperar(lambda c: c.error, 3)
        self.assertIn("Listo", a.error)
        b.enviar("empezar")
        b.esperar(lambda c: c.error, 3)
        self.assertIn("anfitrión", b.error)

    def test_acciones_simultaneas_de_todos(self):
        clientes = self.partida_con(4)
        for c in clientes:
            c.esperar(lambda c: c.arbol is not None, 5)
        barrera = threading.Barrier(4)

        def disparar(c):
            barrera.wait()
            c.decidir([1, 0])

        hilos = [threading.Thread(target=disparar, args=(c,)) for c in clientes]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        for c in clientes:
            self.assertTrue(c.esperar(lambda c: c.resultado is not None, 5))
        self.assertEqual(len(clientes[0].resultado["acciones"]), 4)
        self.assertEqual(len({json.dumps(c.resultado, sort_keys=True) for c in clientes}), 1)

    def test_tiempo_agotado_cuenta_como_sin_respuesta(self):
        clientes = self.partida_con(2, segundos=1)   # el servidor usa al menos 8 s: se acorta abajo
        self.srv.limite = self.srv.reloj() + 0.3
        c = clientes[0]
        self.assertTrue(c.esperar(lambda c: c.resultado is not None, 5))
        self.assertTrue(all(a["accion"] == "sin_respuesta" for a in c.resultado["acciones"]))

    def test_pausa_congela_el_reloj_del_servidor(self):
        clientes = self.partida_con(2)
        a = clientes[0]
        a.esperar(lambda c: c.arbol is not None, 5)
        a.enviar("pausa", pausar=True)
        a.esperar(lambda c: c.estado and c.estado["pausado"], 3)
        congelado = a.estado["restante"]
        time.sleep(0.6)
        self.assertEqual(self.srv._restante(), congelado)
        clientes[1].decidir([0])
        clientes[1].esperar(lambda c: c.error, 2)
        self.assertIn("pausa", clientes[1].error)
        a.enviar("pausa", pausar=False)
        a.esperar(lambda c: c.estado and not c.estado["pausado"], 3)
        self.assertLessEqual(self.srv._restante(), congelado)

    def test_id_repetido_no_duplica_y_puntos_del_cliente_se_ignoran(self):
        clientes = self.partida_con(2)
        a = clientes[0]
        a.esperar(lambda c: c.arbol is not None, 5)
        mensaje = {"tipo": "accion", "id": "fijo-1", "ronda": a.ronda["ronda"], "ruta": [0], "puntos": 9999,
                   "indicadores": {"confianza": 100}}
        for _ in range(3):
            a.sock.sendall(protocolo.codificar(mensaje))
        time.sleep(0.4)
        acciones = [e for e in self.srv.registro if e[0] == "accion"]
        self.assertEqual(len(acciones), 1)
        clientes[1].decidir([2])
        a.esperar(lambda c: c.resultado is not None, 5)
        mio = [x for x in a.resultado["acciones"] if x["jugador"] == a.jugador_id][0]
        self.assertLess(abs(mio["puntos"]), 100)
        self.assertLess(a.resultado["indicadores"]["confianza"], 100)

    def test_mensajes_malformados_no_tumban_el_servidor(self):
        self.srv = servidor()
        crudo = socket.create_connection(("127.0.0.1", self.srv.puerto))
        for linea in (b"esto no es json\n", b"[1,2]\n", b'{"v":99,"tipo":"hola"}\n',
                      b'{"v":1,"tipo":"accion","id":"x","ronda":true,"ruta":[0]}\n',
                      b'{"v":1,"tipo":"hackear","id":"y"}\n'):
            crudo.sendall(linea)
        crudo.settimeout(2)
        datos = b""
        try:
            while datos.count(b"\n") < 5:
                trozo = crudo.recv(4096)
                if not trozo:
                    break
                datos += trozo
        except socket.timeout:
            pass
        errores = [json.loads(l) for l in datos.splitlines() if l]
        self.assertTrue(all(e["tipo"] == "error" for e in errores))
        self.assertEqual(len(errores), 5)
        crudo.close()
        # tras 5 malformados la sesion se cierra, pero el servidor sigue aceptando jugadores
        self.clientes = [unir(self.srv, "ciudadano")]
        self.assertIsNotNone(self.clientes[0].jugador_id)

    def test_desconexion_y_reconexion_con_token(self):
        clientes = self.partida_con(3)
        b = clientes[1]
        b.esperar(lambda c: c.arbol is not None, 5)
        token, jid = b.token, b.jugador_id
        b.sock.close()                                  # corte brusco, sin "salir"
        clientes[0].esperar(lambda c: c.estado and not [j for j in c.estado["jugadores"] if j["id"] == jid][0]["conectado"], 5)
        nuevo = ClienteArena("127.0.0.1", self.srv.puerto)
        nuevo.token = token
        nuevo.reconectar()
        self.clientes.append(nuevo)
        self.assertTrue(nuevo.esperar(lambda c: c.jugador_id == jid and c.arbol is not None, 5))
        nuevo.decidir([2])
        for c in (clientes[0], clientes[2]):
            c.esperar(lambda c: c.arbol is not None, 5)
            c.decidir([2])
        self.assertTrue(clientes[0].esperar(lambda c: c.resultado is not None, 5))
        mio = [x for x in clientes[0].resultado["acciones"] if x["jugador"] == jid][0]
        self.assertEqual(mio["accion"], "ignorar")

    def test_cierre_ordenado_del_servidor(self):
        clientes = self.partida_con(2)
        self.srv.detener()
        for c in clientes:
            self.assertTrue(c.esperar(lambda c: c.cerrado, 5))
        self.assertIn("cerr", clientes[0].cerrado.lower())
        self.srv = None

    def test_un_jugador_se_cae_y_la_ronda_no_se_bloquea(self):
        clientes = self.partida_con(2)
        for c in clientes:
            c.esperar(lambda c: c.arbol is not None, 5)
        clientes[0].decidir([0])
        clientes[1].sock.close()
        self.assertTrue(clientes[0].esperar(lambda c: c.resultado is not None, 5))

    def test_procesos_independientes_2_3_4(self):
        """Clientes como procesos separados del servidor y entre si (como equipos distintos en una LAN)."""
        for n in (2, 3, 4):
            with self.subTest(jugadores=n):
                self.srv = servidor(semilla=7 + n, rondas=3, pausa_resultado=0.3)
                tmp = tempfile.mkdtemp(prefix="arena_")
                procesos = []
                for i, rol in enumerate(ROLES[:n]):
                    salida = os.path.join(tmp, "%s.json" % rol)
                    procesos.append((salida, subprocess.Popen(
                        [sys.executable, os.path.join(RAIZ, "tests", "arena_bot.py"), "--puerto", str(self.srv.puerto),
                         "--rol", rol, "--politica", ("responsable", "azar")[i % 2], "--salida", salida,
                         "--semilla", str(i), "--limite", "60"])))
                    time.sleep(0.15)
                fin = time.monotonic() + 15
                while time.monotonic() < fin:
                    with self.srv.lock:
                        listos = len(self.srv.listos) >= n
                    if listos:
                        break
                    time.sleep(0.05)
                with self.srv.lock:
                    self.srv._m_empezar(type("S", (), {"jid": self.srv.anfitrion})(), {})
                datos = []
                for salida, p in procesos:
                    p.wait(timeout=90)
                    with open(salida, encoding="utf-8") as f:
                        datos.append(json.load(f))
                self.assertTrue(all(d["termino"] for d in datos), [d.get("cerrado") for d in datos])
                self.assertEqual(len({json.dumps(d["final"], sort_keys=True) for d in datos}), 1)
                self.assertEqual(len(datos[0]["final"]["ranking"]), n)
                self.srv.detener()
                self.srv = None


if __name__ == "__main__":
    unittest.main()
