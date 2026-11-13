"""
Duelo de Frecuencias en la Arena Online: contrato entre el servidor y el motor ritmico del navegador.

Una sola fuente de reglas:
- chart: game/ritmo/duelo_<modo>_normal.json (el mismo que juega Ren'Py);
- ventanas y valores de juicio: Ritmo.VENTANAS_MS / Ritmo.VALOR_JUICIO, que el servidor ENVIA al navegador
  (el motor JS no tiene numeros propios; tests/test_ritmo_web.py comprueba que juzga igual que Ritmo.Duelo);
- puntuacion: torneo.puntuar_ritmo (la misma del torneo LAN).

Sincronizacion: el servidor fija el instante de inicio (`inicio`) y lo comunica como "faltan X ms" en cada
respuesta. El navegador estima su desfase con el servidor usando la muestra de menor ida y vuelta (RTT/2),
arranca la cancion localmente con Web Audio en ese instante y juzga con el reloj de AUDIO (no con frames ni
con la red). Nunca se envian notas por internet: solo el resultado al final.

Validacion del resultado (reduce trampas y errores):
- longitud exacta del chart, dificultad Normal;
- cada juicio coherente con su desvio en ms (perfect <= 45 < good <= 90 < bad <= 135; miss sin desvio);
- no se puede entregar una nota antes de que suene (inicio + tiempo de la nota - ventana - tolerancia);
- calibracion acotada;
- patron no humano (desvios casi identicos en muchas notas) -> rechazado.
"""
import json
import os
import random

from clases.Ritmo import VENTANAS_MS, VALOR_JUICIO, validar_chart
from clases.arena.torneo import puntuar_ritmo, ResultadoInvalido

RITMO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ritmo")
PREPARACION_S = 9.0          # cuenta atras comun: da tiempo a descargar el audio y a sincronizar el reloj
MARGEN_FIN_S = 12.0          # despues de la cancion, tiempo para que llegue el resultado
TOLERANCIA_SYNC_MS = 1500    # error maximo admitido en la estimacion del reloj del cliente
CALIBRACION_MAX_MS = 300
MIN_NOTAS_HEURISTICA = 20
DESVIACION_HUMANA_MIN_MS = 2.5
JUICIOS = ("perfect", "good", "bad", "miss")


def cargar_chart(modo):
    with open(os.path.join(RITMO_DIR, "duelo_%s_normal.json" % modo), encoding="utf-8") as f:
        chart = json.load(f)
    errores = validar_chart(chart)
    if errores:
        raise ValueError("chart invalido: %s" % errores[:3])
    return chart


def config_cliente(modo):
    """Todo lo que necesita el motor del navegador (sin numeros duplicados en JS)."""
    chart = cargar_chart(modo)
    return {"modo": modo, "chart": chart, "ventanas": dict(VENTANAS_MS), "valores": dict(VALOR_JUICIO),
            "combo_rompe": ["bad", "miss"], "audio": ["/static/ritmo/duelo_%s.m4a" % modo, "/static/ritmo/duelo_%s.ogg" % modo],
            "preparacion_s": PREPARACION_S, "margen_fin_s": MARGEN_FIN_S, "calibracion_max_ms": CALIBRACION_MAX_MS}


def juicio_de_desvio(d):
    a = abs(d)
    if a <= VENTANAS_MS["perfect"]:
        return "perfect"
    if a <= VENTANAS_MS["good"]:
        return "good"
    if a <= VENTANAS_MS["bad"]:
        return "bad"
    return None


def validar_y_puntuar(chart, datos, transcurrido_ms):
    """transcurrido_ms: ms desde el inicio oficial de la cancion hasta que llego el resultado al servidor."""
    if not isinstance(datos, dict):
        raise ResultadoInvalido("Resultado inválido.")
    juicios, desvios = datos.get("juicios"), datos.get("desvios")
    base = puntuar_ritmo({}, datos, chart=chart)
    if not isinstance(desvios, list) or len(desvios) != len(juicios):
        raise ResultadoInvalido("Faltan los desvíos de cada nota.")
    cal = datos.get("calibracion_ms", 0)
    if isinstance(cal, bool) or not isinstance(cal, (int, float)) or abs(cal) > CALIBRACION_MAX_MS:
        raise ResultadoInvalido("Calibración fuera de rango.")
    ultima = None
    for i, (j, d) in enumerate(zip(juicios, desvios)):
        if j == "miss":
            if d is not None:
                raise ResultadoInvalido("Una nota fallada no puede tener desvío.")
            continue
        # El desvio viaja redondeado a ms: en la frontera de una ventana se admite el redondeo (+-1 ms).
        if isinstance(d, bool) or not isinstance(d, (int, float)) or j not in (
                juicio_de_desvio(abs(d) - 1), juicio_de_desvio(d), juicio_de_desvio(abs(d) + 1)):
            raise ResultadoInvalido("El juicio de la nota %d no corresponde a su desvío." % (i + 1))
        ultima = chart["notes"][i]["time_ms"] + d
    if ultima is not None and transcurrido_ms < ultima - VENTANAS_MS["bad"] - TOLERANCIA_SYNC_MS:
        raise ResultadoInvalido("Llegó un resultado antes de que sonaran sus notas.")
    tocadas = [d for d in desvios if d is not None]
    if len(tocadas) >= MIN_NOTAS_HEURISTICA:
        media = sum(tocadas) / float(len(tocadas))
        dispersion = (sum((d - media) ** 2 for d in tocadas) / len(tocadas)) ** 0.5
        if dispersion < DESVIACION_HUMANA_MIN_MS:
            raise ResultadoInvalido("Patrón de pulsaciones imposible para una persona.")
    else:
        dispersion = None
    base["detalle"].update(calibracion_ms=int(cal), dispersion_ms=None if dispersion is None else round(dispersion, 1),
                           latencia_ms=datos.get("latencia_ms") if isinstance(datos.get("latencia_ms"), (int, float)) else None)
    return base


def payload_bot(chart, nivel, rng):
    """Jugador automatico: desvios gaussianos, juicio derivado del desvio (igual que un navegador)."""
    juicios, desvios = [], []
    sigma = 25 + (1 - nivel) * 90
    for _ in chart["notes"]:
        if rng.random() > 0.35 + nivel * 0.63:
            juicios.append("miss")
            desvios.append(None)
            continue
        d = int(round(rng.gauss(0, sigma)))
        j = juicio_de_desvio(d)
        juicios.append(j or "miss")
        desvios.append(d if j else None)
    return {"dificultad": "normal", "juicios": juicios, "desvios": desvios, "calibracion_ms": 0}


def bot_rng(semilla, jid):
    return random.Random("duelo|%s|%s" % (semilla, jid))
