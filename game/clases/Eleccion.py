"""
Escrutinio del modo Historia (rubrica §3 y §12): cuatro candidatos, participacion, votos, abstencion,
ganador y explicacion, calculados a partir de los indicadores de la ciudad y la reputacion del alcalde.

Es coherente con el final narrativo ya decidido (clases/Destinos.py): no lo sustituye, lo cuantifica.
- mandato:  el alcalde gana con holgura (gracias al audio falso).
- dividida: resultado apretado entre el alcalde y Tomas Vega (unos 4.000 votos).
- caos:     escrutinio impugnado: hay cifras, pero ningun resultado aceptado.
- informada / secreto: gana quien la ciudad informada elige; el alcalde puede ganar o perder limpio.
"""
import random

CANDIDATOS_HISTORIA = (("alcalde", "Tú (alcalde)"), ("vega", "Tomás Vega"), ("ortega", "Juan Ortega"), ("ruiz", "Elena Ruiz"))
ELECTORES = 120000


def _clamp(v, a=0.0, b=100.0):
    return max(a, min(b, v))


def escrutinio_historia(final, indicadores, reputacion, semilla=0):
    ind = indicadores
    rng = random.Random("escrutinio|%s|%s" % (semilla, final))
    participacion = _clamp(38 + 0.25 * ind["confianza"] + 0.15 * ind["bienestar"] - 0.15 * ind["conflictos"], 30, 82)
    votantes = int(ELECTORES * participacion / 100)
    # Apoyo base: el alcalde vive de su credibilidad y de la confianza; Vega capitaliza el enojo y el caos.
    apoyo = {
        "alcalde": 20 + 0.35 * reputacion + 0.20 * ind["confianza"] - 0.20 * ind["desinformacion"],
        "vega": 25 + 0.15 * ind["conflictos"] + 0.10 * ind["desinformacion"] + 0.10 * ind["info_verificada"],
        "ortega": 14 + 0.10 * ind["convivencia"],
        "ruiz": 10 + 0.08 * ind["bienestar"],
    }
    if final == "mandato":
        apoyo["alcalde"] = max(apoyo.values()) * 1.35
    elif final == "dividida":
        apoyo["alcalde"] = apoyo["vega"] = max(apoyo["alcalde"], apoyo["vega"])
    for c in apoyo:
        apoyo[c] = max(1.0, apoyo[c] * rng.uniform(0.97, 1.03))
    total = sum(apoyo.values())
    votos = {c: int(votantes * apoyo[c] / total) for c in apoyo}
    if final == "dividida":
        nuevo = votos["alcalde"] - 4000 if rng.random() < 0.5 else votos["alcalde"] + 4000
        votos["ortega"] -= nuevo - votos["vega"]   # el total de votantes no cambia
        votos["vega"] = nuevo
    ganador = max(votos, key=votos.get)
    impugnado = final == "caos"

    explicacion = ["Participación del %d%%: votaron %s de %s personas." % (
        participacion, "{:,}".format(votantes).replace(",", "."), "{:,}".format(ELECTORES).replace(",", "."))]
    if ind["confianza"] >= 60:
        explicacion.append("La confianza ciudadana alta (%d) llevó a más gente a votar." % ind["confianza"])
    elif ind["confianza"] < 40:
        explicacion.append("Con la confianza baja (%d), mucha gente se quedó en casa." % ind["confianza"])
    if ind["desinformacion"] >= 55:
        explicacion.append("La desinformación (%d) restó votos a quien gobernaba y alimentó el enojo." % ind["desinformacion"])
    elif ind["desinformacion"] <= 30:
        explicacion.append("Con la desinformación contenida (%d), se votó por propuestas y no por rumores." % ind["desinformacion"])
    explicacion.append("Tu credibilidad terminó en %d/100." % reputacion)
    if final == "mandato":
        explicacion.append("El audio falso contra Tomás Vega inclinó la balanza: ganaste, pero con una mentira.")
    elif final == "dividida":
        explicacion.append("Cuatro mil votos de diferencia: media ciudad celebra y la otra media sospecha.")
    elif impugnado:
        explicacion.append("Cada bando tiene sus propias cifras: el escrutinio quedó impugnado.")
    return {"candidatos": [{"id": c, "nombre": n, "votos": votos[c]} for c, n in CANDIDATOS_HISTORIA],
            "participacion": round(participacion), "votantes": votantes, "abstencion": ELECTORES - votantes,
            "ganador": None if impugnado else ganador,
            "ganador_nombre": None if impugnado else dict(CANDIDATOS_HISTORIA)[ganador],
            "impugnado": impugnado, "explicacion": explicacion}
