class Ciudad:

    def __init__(self):
        self.info_verificada = 50
        self.confianza = 60
        self.convivencia = 70
        self.bienestar = 65
        self.desinformacion = 30
        self.conflictos = 20

    # ===== GETTERS =====

    def get_info_verificada(self):
        return self.info_verificada

    def get_confianza(self):
        return self.confianza

    def get_convivencia(self):
        return self.convivencia

    def get_bienestar(self):
        return self.bienestar

    def get_desinformacion(self):
        return self.desinformacion

    def get_conflictos(self):
        return self.conflictos

    # ===== ACCIONES =====

    def verificar(self):
        self.info_verificada = min(100, self.info_verificada + 5)
        self.confianza = min(100, self.confianza + 3)
        self.desinformacion = max(0, self.desinformacion - 4)

    def compartir(self, es_verificada):
        if es_verificada:
            self.confianza = min(100, self.confianza + 2)
            self.bienestar = min(100, self.bienestar + 1)
        else:
            self.desinformacion = min(100, self.desinformacion + 5)
            self.conflictos = min(100, self.conflictos + 3)
            self.convivencia = max(0, self.convivencia - 3)

    def reportar(self):
        self.conflictos = max(0, self.conflictos - 2)
        self.info_verificada = min(100, self.info_verificada + 2)

    def ignorar(self, tipo):
        if tipo in ("FALSA", "RUMOR"):
            self.desinformacion = min(100, self.desinformacion + 3)
            self.conflictos = min(100, self.conflictos + 2)

    # ===== CONDICIONES DE JUEGO =====

    def derrota_inmediata(self):
        if self.desinformacion >= 80:
            return "La desinformacion llego al 80%.\nCiudad Nova entro en panico informativo."
        if self.conflictos >= 80:
            return "Los conflictos activos llegaron al 80%.\nLa convivencia digital colapso."
        if self.confianza <= 20:
            return "La confianza cayo a 20 o menos.\nLos ciudadanos dejaron de creer en sus instituciones."
        return None

    def victoria(self, jugador):
        return (
            self.info_verificada >= 50 and
            self.confianza >= 50 and
            self.convivencia >= 50 and
            self.bienestar >= 50 and
            self.desinformacion <= 50 and
            self.conflictos <= 40 and
            jugador.reputacion >= 60 and
            jugador.puntos >= 50
        )
