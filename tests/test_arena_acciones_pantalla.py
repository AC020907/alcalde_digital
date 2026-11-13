"""Regresion: en Ren'Py, una accion Function(f) cuyo f devuelve algo distinto de None TERMINA la pantalla con
ese valor. ClienteArena.enviar() devuelve el id del mensaje, asi que un boton con Function(c.enviar, ...)
cerraba `call screen arena_partida` y el bucle de la Arena salia al menu ("se cierra al pulsar Siguiente
ronda"). Los botones de la Arena deben usar arena_enviar(), que no devuelve nada."""
import os
import re
import unittest

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "game"))
ARCHIVOS = [os.path.join(RAIZ, "arena", n) for n in ("arena.rpy", "arena_torneo.rpy")]
METODOS_CON_VALOR = r"(enviar|decidir|entregar_prueba|unirse|esperar|procesar)"


class AccionesDePantallaArena(unittest.TestCase):
    def test_ningun_boton_llama_directo_a_un_metodo_del_cliente_que_devuelve_valor(self):
        patron = re.compile(r"Function\(\s*(c|AS\.cliente)\." + METODOS_CON_VALOR + r"\b")
        hallados = []
        for ruta in ARCHIVOS:
            with open(ruta, encoding="utf-8") as f:
                for n, linea in enumerate(f, 1):
                    if patron.search(linea):
                        hallados.append("%s:%d" % (os.path.basename(ruta), n))
        self.assertEqual(hallados, [], "Botones que cerrarian la pantalla de la Arena: %s" % hallados)

    def test_arena_enviar_existe_y_no_devuelve_el_id(self):
        with open(ARCHIVOS[0], encoding="utf-8") as f:
            fuente = f.read()
        m = re.search(r"def arena_enviar\(tipo, \*\*datos\):\n((?:        .*\n)+)", fuente)
        self.assertIsNotNone(m, "falta arena_enviar en arena.rpy")
        self.assertNotIn("return", m.group(1))


if __name__ == "__main__":
    unittest.main()
