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
