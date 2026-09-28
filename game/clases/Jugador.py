class Jugador:

    ROLES = {
        "Ciudadano":  {"amplificador": 1.0, "desc": "Interactua con la informacion y contribuye al bienestar general."},
        "Periodista":  {"amplificador": 1.5, "desc": "Detecta noticias falsas con mayor rapidez y precision."},
        "Influencer":  {"amplificador": 2.0, "desc": "Sus decisiones tienen mayor alcance de propagacion en Civitas."},
        "Candidato":   {"amplificador": 1.2, "desc": "Construye confianza y puede responder publicaciones directamente."},
    }

    def __init__(self, nombre, rol="Ciudadano"):
        self.nombre = nombre
        self.rol = rol
        self.puntos = 0
        self.reputacion = 50

    # ===== GETTERS =====

    def get_nombre(self):
        return self.nombre

    def get_rol(self):
        return self.rol

    def get_puntos(self):
        return self.puntos

    def get_reputacion(self):
        return self.reputacion

    def get_amplificador(self):
        return self.ROLES.get(self.rol, self.ROLES["Ciudadano"])["amplificador"]

    def get_desc_rol(self):
        return self.ROLES.get(self.rol, self.ROLES["Ciudadano"])["desc"]

    # ===== SETTERS =====

    def set_rol(self, rol):
        if rol in self.ROLES:
            self.rol = rol

    # ===== ACCIONES =====

    def ganar_puntos(self, cantidad):
        self.puntos += int(cantidad * self.get_amplificador())
        self.reputacion = min(100, self.reputacion + 2)

    def perder_puntos(self, cantidad):
        self.puntos = max(0, self.puntos - int(cantidad * self.get_amplificador()))
        self.reputacion = max(0, self.reputacion - 2)
