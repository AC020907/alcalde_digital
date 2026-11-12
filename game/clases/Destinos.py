"""
Desenlaces de Alcalde Digital: catalogo del Archivo de Destinos y regla que decide el final.

Logica pura (sin Ren'Py). story/finales.rpy arma el dict de estado y llama a decidir_final().
"""

INFORMADA, DIVIDIDA, CAOS, MANDATO, SECRETO = "informada", "dividida", "caos", "mandato", "secreto"

# Orden de exhibicion en el Archivo de Destinos.
FINALES = (INFORMADA, DIVIDIDA, CAOS, MANDATO, SECRETO)

DESTINOS = {
    INFORMADA: {
        "titulo": "Ciudad Informada",
        "insignia": "Lupa",
        "color": "#2f9e8f",
        "descripcion": "Frenaste la Gran Viralización y la ciudad aprendió a preguntar de dónde viene cada cosa.",
        "misterio": "Una ciudad que verifica antes de creer.",
    },
    DIVIDIDA: {
        "titulo": "Ciudad Dividida",
        "insignia": "Grieta",
        "color": "#d97706",
        "descripcion": "La ciudad sobrevivió a la semana, pero con vecinos que ya no se hablan.",
        "misterio": "Sobrevivir no es lo mismo que sanar.",
    },
    CAOS: {
        "titulo": "Caos Informativo",
        "insignia": "Ruido",
        "color": "#c0392b",
        "descripcion": "Nadie sabe quién ganó. Cada bando tiene sus propias capturas y sus propias verdades.",
        "misterio": "Cuando todo es dudoso, gana quien grita más fuerte.",
    },
    MANDATO: {
        "titulo": "Mandato Prestado",
        "insignia": "Marioneta",
        "color": "#8c2f4b",
        "descripcion": "Ganaste usando un audio falso. Resonancia Consultores te manda la factura.",
        "misterio": "Algunas victorias se pagan después.",
    },
    SECRETO: {
        "titulo": "Fuente Abierta",
        "insignia": "Expediente",
        "color": "#5b5bd6",
        "descripcion": "Publicaste el expediente con todas sus fuentes: la campaña tenía nombre y apellido.",
        "misterio": "Final secreto: sigue las tres pistas decisivas.",
    },
}


def decidir_final(estado):
    """
    estado: dict con
        forzado (str|None), derrota (bool), secreto_publicado (bool), secreto_disponible (bool),
        uso_audio (bool), viral_ok (bool), desinformacion, confianza, reputacion (int 0..100),
        salud_ciudad (int 0..100, ver Puntuacion.puntos_ciudad), falsas_compartidas (int).
    El orden importa: el colapso de la ciudad pesa mas que cualquier victoria, y no se puede
    destapar la maquinaria de rumores despues de haberla usado.
    """
    if estado.get("forzado"):
        return estado["forzado"]
    if estado.get("derrota"):
        return CAOS
    if estado.get("secreto_publicado") and estado.get("secreto_disponible") and not estado.get("uso_audio"):
        return SECRETO
    viral_ok = estado.get("viral_ok", False)
    # Perder el climax con la ciudad ya debilitada es caos; con la ciudad sana, solo la divide.
    if estado["desinformacion"] >= 65 or (not viral_ok and (estado["confianza"] < 50 or estado["desinformacion"] >= 50)):
        return CAOS
    if estado.get("uso_audio"):
        return MANDATO
    if (viral_ok and estado["desinformacion"] <= 45 and estado["confianza"] >= 55
            and estado["reputacion"] >= 55 and estado.get("salud_ciudad", 0) >= 50
            and estado.get("falsas_compartidas", 0) < 2):
        return INFORMADA
    return DIVIDIDA
