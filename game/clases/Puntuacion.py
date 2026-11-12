"""
Puntuacion Civica (0..1000): recompensa decisiones informadas, investigacion y responsabilidad.

Componentes y maximos:
    verificacion  300  respuestas a las publicaciones del telefono (banco AVL), ponderadas por riesgo
    decisiones    250  calidad de las decisiones narrativas clave
    minijuegos    200  calificacion de los cinco minijuegos (incluye el Duelo de Frecuencias)
    investigacion 150  evidencias del expediente
    ciudad        100  estado final de los indicadores

Ningun final garantiza el maximo: la puntuacion se calcula de lo que hizo el jugador, no del final.
Logica pura (sin Ren'Py); el servidor del leaderboard aplica las mismas cotas.
"""

MAXIMOS = {"verificacion": 300, "decisiones": 250, "minijuegos": 200, "investigacion": 150, "ciudad": 100}
TOTAL_MAXIMO = sum(MAXIMOS.values())

# (es_falsa, accion) -> valor 0..1. Compartir algo cierto sin verificar acierta por suerte.
VALOR_ACCION = {
    (False, "verificar_si"): 1.0, (False, "compartir"): 0.6, (False, "ignorar"): 0.3, (False, "verificar_no"): 0.0,
    (True, "verificar_no"): 1.0, (True, "ignorar"): 0.4, (True, "compartir"): 0.0, (True, "verificar_si"): 0.0,
}

# El maximo del componente sigue siendo 200: el Duelo de Frecuencias reparte el peso entre cinco retos.
MINIJUEGOS = ("moderador", "contencion", "rastreador", "viralizacion", "ritmo")
VALOR_NOTA = {"S": 1.0, "A": 0.85, "B": 0.7, "C": 0.5, "D": 0.3}
VALOR_FALLO = 0.15

PUNTOS_GRUPO_CLAVE = 30
PUNTOS_PISTA_EXTRA = 6
TOPE_PISTAS_EXTRA = 60


def puntos_verificacion(decisiones_pub):
    """decisiones_pub: lista de (nivel_riesgo, es_falsa, accion)."""
    if not decisiones_pub:
        return 0
    suma = peso_total = 0.0
    for riesgo, es_falsa, accion in decisiones_pub:
        peso = 1.0 + riesgo / 50.0
        suma += peso * VALOR_ACCION.get((bool(es_falsa), accion), 0.0)
        peso_total += peso
    return int(round(MAXIMOS["verificacion"] * suma / peso_total))


def puntos_decisiones(calidades):
    """calidades: dict id_decision -> valor 0..1 (una entrada por decision tomada)."""
    if not calidades:
        return 0
    media = sum(max(0.0, min(1.0, v)) for v in calidades.values()) / len(calidades)
    return int(round(MAXIMOS["decisiones"] * media))


def valor_minijuego(resultado):
    if not resultado:
        return 0.0
    if not resultado.get("exito"):
        return VALOR_FALLO
    nota = resultado.get("calificacion") or ("S" if resultado.get("perfecto") else "A")
    return VALOR_NOTA.get(nota, VALOR_NOTA["C"])


def puntos_minijuegos(registro):
    """registro: dict minijuego -> resultado; un minijuego no jugado vale 0."""
    total = sum(valor_minijuego(registro.get(m)) for m in MINIJUEGOS)
    return int(round(MAXIMOS["minijuegos"] * total / len(MINIJUEGOS)))


def puntos_investigacion(pistas, grupos_clave):
    """pistas: ids en el expediente; grupos_clave: dict grupo -> (ids que lo cumplen)."""
    pistas = set(pistas)
    cumplidos = [g for g, ids in grupos_clave.items() if pistas & set(ids)]
    usadas = set()
    for g in cumplidos:
        usadas |= pistas & set(grupos_clave[g])
    extra = min(TOPE_PISTAS_EXTRA, PUNTOS_PISTA_EXTRA * len(pistas - usadas))
    return min(MAXIMOS["investigacion"], PUNTOS_GRUPO_CLAVE * len(cumplidos) + extra)


def puntos_ciudad(info_verificada, confianza, convivencia, bienestar, desinformacion, conflictos):
    salud = (info_verificada + confianza + convivencia + bienestar + (100 - desinformacion) + (100 - conflictos)) / 6.0
    return int(round(max(0.0, min(100.0, salud))))


def calcular(decisiones_pub, calidades, registro, pistas, grupos_clave, indicadores, final=None):
    """indicadores: dict con las seis claves de la ciudad. Devuelve {componentes..., 'total'}."""
    componentes = {
        "verificacion": puntos_verificacion(decisiones_pub),
        "decisiones": puntos_decisiones(calidades),
        "minijuegos": puntos_minijuegos(registro),
        "investigacion": puntos_investigacion(pistas, grupos_clave),
        "ciudad": puntos_ciudad(**indicadores),
    }
    # Una ciudad en caos no puede puntuar como sana (el servidor exige la misma cota).
    if final == "caos":
        componentes["ciudad"] = min(componentes["ciudad"], 50)
    for clave, maximo in MAXIMOS.items():
        componentes[clave] = max(0, min(maximo, componentes[clave]))
    componentes["total"] = sum(componentes[c] for c in MAXIMOS)
    return componentes
