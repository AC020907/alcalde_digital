## Misiones principales: que hacer y a que lugar del mapa ir.
## Es solo el catalogo y la logica de estado; la historia marca cada mision como hecha
## (completar_mision en story/misiones.rpy) y el mapa muestra la activa.

PROLOGO, LUNES, MIERCOLES, VIERNES, DOMINGO = range(5)

# (id, momento, titulo, descripcion, ubicacion del mapa, minijuego o None, entra en Modo Feria)
_MISIONES = (
    ("lunes_plaza", LUNES, "Calma la plaza",
     "El rumor del agua llena la plaza. Habla con la gente y revisa qué se comenta en CivitasNet.",
     "alcaldia", None, True),
    ("lunes_martina", LUNES, "Ayuda a Martina",
     "Sus comentarios están llenos de bots. Bórralos, pero deja en paz a quien critica de verdad.",
     "centro", "Moderación Express", True),
    ("lunes_noche", LUNES, "Vuelve a la Alcaldía",
     "Termina el primer día. Claudia te espera en el balcón con algo raro que encontró en CivitasNet.",
     "alcaldia", None, False),
    ("mie_barrio_sur", MIERCOLES, "Frena el rumor del Barrio Sur",
     "Rodrigo dice que mañana cierran el hospital. Intercepta el rumor antes de que llegue a toda la ciudad.",
     "barrio_sur", "Caza-Rumores", True),
    ("mie_operaciones", MIERCOLES, "Reúnete con tu equipo",
     "Claudia reúne a todos en el centro de operaciones para decidir cómo responder.",
     "alcaldia", None, False),
    ("vie_redaccion", VIERNES, "Visita la redacción",
     "Claudia encontró un patrón: todos los rumores salen de la misma red. Escucha lo que descubrió.",
     "prensa", None, True),
    ("vie_rastreo", VIERNES, "Rastrea el origen del rumor",
     "Ordena las fichas de cada cuenta y reconstruye la cadena hasta quien lo empezó.",
     "alcaldia", "Rastreador", False),
    ("dom_elecciones", DOMINGO, "Defiende la ciudad",
     "Las cuentas falsas despiertan a la vez, dos horas antes de abrir las urnas. No las dejes ganar.",
     "alcaldia", "La Gran Viralización", True),
)

# Modo Feria: solo estos viajes se conducen; en los demas el carro llega directo para no alargar la demo.
FERIA_CONDUCIR = ("lunes_martina", "mie_barrio_sur", "vie_redaccion")

MISIONES = tuple(
    {"id": i, "momento": mo, "titulo": t, "descripcion": d, "ubicacion": u, "minijuego": mj, "feria": f}
    for i, mo, t, d, u, mj, f in _MISIONES
)
POR_ID = {m["id"]: m for m in MISIONES}


def misiones_de(feria=False):
    return [m for m in MISIONES if m["feria"] or not feria]


def mision_activa(hechas, feria=False):
    """Primera mision sin completar (en orden de historia), o None si ya no queda ninguna."""
    for m in misiones_de(feria):
        if m["id"] not in hechas:
            return m
    return None


def estado_misiones(hechas, feria=False):
    """Lista de (mision, estado): 'hecha', 'activa' (la siguiente de la historia) o 'bloqueada'."""
    activa = mision_activa(hechas, feria)
    lista = []
    for m in misiones_de(feria):
        if m["id"] in hechas:
            estado = "hecha"
        elif m is activa:
            estado = "activa"
        else:
            estado = "bloqueada"
        lista.append((m, estado))
    return lista
