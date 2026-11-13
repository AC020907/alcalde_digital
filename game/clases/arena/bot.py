"""
Jugador automatico de la Arena: un cliente TCP de verdad, en su propio hilo.

Lo usa el anfitrion para completar la sala cuando faltan personas (aparece como "(bot)") y lo usan las
pruebas. Decide leyendo lo mismo que ve una persona: el arbol de su rol y la pista o fuente que muestra.
"""
import random
import threading
import time

from clases.arena.cliente import ClienteArena
from clases.arena.torneo import payload_bot

SENALES_DE_ALERTA = ("no tiene fecha", "me lo contaron", "exageración", "mayúsculas", "no muestra",
                     "no hay ninguna", "no hay ningún", "sintético", "montaje", "insulta", "no afirma")


def elegir_ruta(arbol, politica, rng):
    etiquetas = [h["etiqueta"] for h in arbol["hijos"]]
    if politica == "azar":
        i = rng.randrange(len(etiquetas))
        ruta = [i]
        if arbol["hijos"][i]["hijos"]:
            ruta.append(rng.randrange(len(arbol["hijos"][i]["hijos"])))
        return ruta
    if politica == "irresponsable":
        return [etiquetas.index("compartir")]
    if "responder" in etiquetas:
        return [etiquetas.index("responder")]
    verificar = etiquetas.index("verificar")
    texto = arbol["hijos"][verificar]["texto"].lower()
    if "opinión" in texto or "habla de gustos" in texto or "para mí" in texto:
        return [etiquetas.index("ignorar")]
    sospecha = any(p in texto for p in SENALES_DE_ALERTA)
    return [verificar, 1 if sospecha else 0]


class BotArena(object):
    def __init__(self, host, puerto, rol, nombre=None, politica="responsable", semilla=0, demora=(1.5, 4.0), nivel=None):
        self.cliente = ClienteArena(host, puerto)
        self.rol, self.nombre = rol, nombre or "%s (bot)" % rol.capitalize()
        self.politica, self.rng, self.demora = politica, random.Random(semilla), demora
        self.nivel = nivel if nivel is not None else {"responsable": .8, "azar": .5}.get(politica, .3)
        self.activo = False

    def iniciar(self):
        self.cliente.conectar()
        self.cliente.unirse(self.nombre, self.rol)
        self.activo = True
        threading.Thread(target=self._bucle, daemon=True).start()
        return self

    def detener(self):
        self.activo = False
        self.cliente.cerrar()

    def _bucle(self):
        c, hechas, listo = self.cliente, set(), False
        while self.activo and not c.cerrado:
            c.procesar()
            if c.jugador_id and not listo:
                c.enviar("listo", listo=True)
                listo = True
            if c.ronda and c.arbol and c.ronda["ronda"] not in hechas:
                hechas.add(c.ronda["ronda"])
                time.sleep(self.rng.uniform(*self.demora))   # como una persona: no contesta al instante
                c.decidir(elegir_ruta(c.arbol, self.politica, self.rng))
            if c.prueba and ("p", c.prueba["indice"]) not in hechas:
                hechas.add(("p", c.prueba["indice"]))
                time.sleep(self.rng.uniform(*self.demora))
                try:
                    c.entregar_prueba(payload_bot(c.prueba, self.nivel, self.rng))
                except OSError:   # se detuvo el bot mientras "jugaba"
                    return
            time.sleep(0.05)
