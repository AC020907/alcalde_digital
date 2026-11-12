"""
Duelo de Frecuencias: cancion original + charts generados de LOS MISMOS eventos que suenan.

Estructura de llamada y respuesta: NOVA lanza una frase con sintetizador digital (no se toca) y la
"senal" de Ciudad Nova responde con el mismo ritmo (esas son las notas del chart). 120 BPM: 500 ms
por pulso, sin humanizacion en las capas que se juegan, asi el chart esta sincronizado por construccion.

Uso:  python tools/musica/duelo.py      ->  game/assets/audio/music/duelo_{historia,feria}.ogg
                                             game/ritmo/duelo_{historia,feria}_{normal,facil}.json
"""
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import instruments as I  # noqa: E402
from componer import master, write_ogg  # noqa: E402
from dsp import mtof  # noqa: E402
from song import Song  # noqa: E402

RAIZ = AQUI.parent.parent
BPM = 120
MS_PULSO = 60000 / BPM
ESCALA = [57, 60, 62, 64, 67, 69, 72, 74]  # La menor pentatonica + octava: suena "Ciudad Nova" sin chocar

# Frases de 2 compases (8 pulsos): (pulso, grado). La respuesta repite el ritmo de la llamada.
FRASES = {
    "intro":    [(0, 0), (2, 2), (4, 3), (6, 4)],
    "a":        [(0, 0), (1, 2), (2, 3), (3, 2), (4, 4), (5, 3), (6, 2), (6.5, 1), (7, 0)],
    "b":        [(0, 4), (0.5, 3), (1, 2), (2, 4), (3, 5), (4, 4), (4.5, 3), (5, 2), (6, 1), (7, 0)],
    "c":        [(0, 2), (0.5, 3), (1, 4), (1.5, 5), (2, 4), (3, 2), (3.5, 3), (4, 5), (5, 6), (5.5, 5), (6, 4), (7, 2)],
    "d":        [(0, 5), (0.25, 6), (0.5, 5), (1, 4), (1.5, 3), (2, 4), (2.5, 5), (3, 6), (4, 7), (4.5, 6), (5, 5),
                 (5.5, 4), (6, 3), (6.5, 2), (7, 0)],
}
# (compas de inicio, frase, quien): "nova" llama, "senal" responde (jugable).
PLAN_HISTORIA = [(2, "intro", "senal")] + [
    (4 + 4 * k, frase, quien) for k, frase in enumerate(["a", "a", "b", "b", "c", "c", "d"]) for quien in ("nova",)
] + [(6 + 4 * k, frase, "senal") for k, frase in enumerate(["a", "a", "b", "b", "c", "c", "d"])] + [
    (32, "d", "senal")]
PLAN_FERIA = [(2, "intro", "senal")] + [(4 + 4 * k, f, "nova") for k, f in enumerate(["b", "c", "d"])] + \
             [(6 + 4 * k, f, "senal") for k, f in enumerate(["b", "c", "d"])]
COMPASES = {"historia": 36, "feria": 18}
PLANES = {"historia": PLAN_HISTORIA, "feria": PLAN_FERIA}


def carril_de(grado):
    # La altura decide el carril: grave a la izquierda, agudo a la derecha (como leer una partitura).
    return min(3, grado * 4 // len(ESCALA))


def construir(modo):
    bars = COMPASES[modo]
    s = Song("duelo_" + modo, BPM, bars, rt60=1.4, seed=11, hum=0.0)
    notas = []
    for bar0, nombre, quien in PLANES[modo]:
        for pulso, grado in FRASES[nombre]:
            beat = bar0 * 4 + pulso
            if quien == "nova":
                s.put(I.digi_arp(mtof(ESCALA[grado] + 12), 0.4 * s.spb, 0.7, bits=5, hold=2), beat, -0.35, 0.34, 0.25, hum=0.0)
            else:
                s.put(I.pluck(mtof(ESCALA[grado] + 12), 0.45 * s.spb, 0.9, tau=0.22, bright=0.75), beat, 0.15, 0.8, 0.15, hum=0.0)
                notas.append({"time_ms": int(round(beat * MS_PULSO)), "lane": carril_de(grado), "type": "tap", "pulso": beat})
    # Pulso firme y marcado de compas: el jugador siente el tiempo aunque no lea las notas.
    s.drums(0, bars - 2, {"k": "x...x...x...x...", "h": "..x...x...x...x."}, gain=0.36)
    s.drums(4, bars - 2, {"s": "....x.......x..."}, gain=0.42)
    s.drums(0, 2, {"t": "x...x...x...x..."}, gain=0.45)  # cuenta atras audible: 8 pulsos antes de la primera nota
    progresion = ["Am", "F", "C", "G"]
    from song import voice
    for bar in range(2, bars - 2):
        for m in voice(progresion[bar % 4], 52):
            s.put(I.pad(mtof(m), 4 * s.spb, 0.5, bright=0.3), bar * 4, 0, 0.07, 0.5, hum=0.0)
        s.put(I.bass(mtof(45 + {"Am": 0, "F": -4, "C": 3, "G": -2}[progresion[bar % 4]]), 1.8 * s.spb, 0.8), bar * 4, 0, 0.42, 0.05, hum=0.0)
    final = (bars - 2) * 4
    for m in (57, 64, 69, 72):
        s.put(I.stab(mtof(m), 2.5 * s.spb, 0.9), final, 0, 0.3, 0.4, hum=0.0)
    s.put(I.sub_boom(0.8, 45.0), final, 0, 0.5, 0.1, hum=0.0)
    notas.append({"time_ms": int(round(final * MS_PULSO)), "lane": 1, "type": "tap", "pulso": final})
    notas.append({"time_ms": int(round(final * MS_PULSO)), "lane": 2, "type": "tap", "pulso": final})
    return s, sorted(notas, key=lambda n: (n["time_ms"], n["lane"]))


def chart(modo, notas, dificultad, duracion_ms):
    if dificultad == "facil":
        # Solo los pulsos enteros y sin acordes: jugable con un dedo y en pantallas tactiles.
        vistas, usadas = [], set()
        for n in notas:
            if float(n["pulso"]).is_integer() and n["time_ms"] not in usadas:
                vistas.append(n)
                usadas.add(n["time_ms"])
        notas = vistas
    return {"song_id": "duelo_" + modo, "version": 1, "bpm": BPM, "offset_ms": 0, "difficulty": dificultad,
            "duration_ms": int(duracion_ms), "notes": [{k: n[k] for k in ("time_ms", "lane", "type")} for n in notas]}


def main():
    destino_charts = RAIZ / "game" / "ritmo"
    destino_charts.mkdir(parents=True, exist_ok=True)
    for modo in ("historia", "feria"):
        s, notas = construir(modo)
        audio = s.render()
        # La cola de reverb no debe envolver al inicio (no es un bucle): se corta con fundido.
        out = master(audio, -16.0)
        n = len(out)
        fade = int(0.6 * 44100)
        out[-fade:] *= np.linspace(1, 0, fade)[:, None]
        write_ogg(RAIZ / "game" / "assets" / "audio" / "music" / ("duelo_%s.ogg" % modo), out)
        duracion_ms = n / 44100 * 1000
        for dif in ("normal", "facil"):
            c = chart(modo, notas, dif, duracion_ms)
            (destino_charts / ("duelo_%s_%s.json" % (modo, dif))).write_text(json.dumps(c, indent=1), encoding="utf-8")
            print("%-8s %-7s %5.1f s  %3d notas" % (modo, dif, duracion_ms / 1000, len(c["notes"])))


if __name__ == "__main__":
    main()
