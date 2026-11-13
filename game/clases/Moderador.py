from collections import deque


class ColaModeracion:
    """
    Minijuego 2 - Moderador en tiempo real. Los comentarios reportados llegan a
    una cola FIFO (deque): siempre se atiende el mas antiguo. El jugador decide
    borrar o aprobar antes de que se acabe el tiempo de cada tarjeta.
    Cada elemento debe tener: autor, contenido, es_falsa (True = bot/desinformacion).
    """

    def __init__(self, publicaciones, tiempo_por_tarjeta=4.2, tiempo_minimo=1.8,
                 vidas=3, cuenta_regresiva=3.0):
        self.cola = deque(publicaciones)
        self.total = len(self.cola)
        self.tiempo_base = tiempo_por_tarjeta
        self.tiempo_minimo = tiempo_minimo
        self.vidas = vidas
        self.intro = cuenta_regresiva
        self.actual = None
        self.tiempo_tarjeta = 0.0
        self.tiempo_restante = 0.0
        self.aciertos = 0
        self.errores = 0
        self.racha = 0
        self.mejor_racha = 0
        self.puntos = 0
        self.atendidas = 0
        self.historial = []
        self.ultimo = None             # (texto, correcto) para el feedback visual
        self.siguiente()

    def siguiente(self):
        self.actual = self.cola.popleft() if self.cola else None
        self.tiempo_tarjeta = max(self.tiempo_minimo, self.tiempo_base - 0.12 * self.aciertos)
        self.tiempo_restante = self.tiempo_tarjeta
        return self.actual

    def pendientes(self):
        return len(self.cola)

    def progreso_tiempo(self):
        return max(0.0, self.tiempo_restante / self.tiempo_tarjeta) if self.tiempo_tarjeta else 0.0

    def jugando(self):
        return self.intro <= 0 and not self.terminado()

    def _registrar(self, correcto, texto):
        self.atendidas += 1
        if correcto:
            self.aciertos += 1
            self.racha += 1
            self.mejor_racha = max(self.mejor_racha, self.racha)
            ganados = 10 * (1 + self.racha // 3)
            self.puntos += ganados
            self.ultimo = ("%s  +%d" % (texto, ganados), True)
        else:
            self.errores += 1
            self.racha = 0
            self.vidas -= 1
            self.ultimo = (texto, False)

    def decidir(self, eliminar):
        if not self.jugando() or self.actual is None:
            return False
        correcto = (eliminar == self.actual.es_falsa)
        if correcto:
            texto = "BORRADO" if eliminar else "APROBADO"
        else:
            texto = "ERA UN USUARIO REAL" if eliminar else "SE TE COLÓ UN BOT"
        self.historial.append((self.actual, eliminar, correcto))
        self._registrar(correcto, texto)
        self.siguiente()
        return correcto

    def tick(self, dt):
        if self.terminado():
            return
        if self.intro > 0:
            self.intro -= dt
            return
        self.tiempo_restante -= dt
        if self.tiempo_restante <= 0:
            if self.actual.es_falsa:
                self.historial.append((self.actual, False, False))
                self._registrar(False, "TIEMPO: EL BOT SE QUEDÓ")
            else:
                self.historial.append((self.actual, False, True))
                self._registrar(True, "APROBADO")
            self.siguiente()

    def terminado(self):
        return self.actual is None or self.vidas <= 0

    def exito(self):
        return self.vidas > 0 and self.aciertos >= self.total * 0.6

    def resultado(self):
        exito = self.exito()
        if exito and self.errores == 0:
            consecuencia = {"desinformacion": -6, "info_verificada": 4, "confianza": 2, "puntos": 2 * self.aciertos}
        elif exito:
            consecuencia = {"desinformacion": -3, "info_verificada": 2, "puntos": 2 * self.aciertos}
        else:
            consecuencia = {"desinformacion": 4, "confianza": -2}
        return {
            "minijuego": "moderador",
            "exito": exito,
            "perfecto": exito and self.errores == 0,
            "aciertos": self.aciertos,
            "errores": self.errores,
            "puntos": self.puntos,
            "mejor_racha": self.mejor_racha,
            "mensaje": "Moderaste %d de %d comentarios correctamente." % (self.aciertos, self.total),
            "consecuencia": consecuencia,
        }
