"""
Auditoria objetiva del doblaje: transcribe cada linea con Vosk (reconocedor offline en español) y la
compara con el texto que se le dio al TTS. Tambien mide la señal: silencios internos largos,
saturacion, sonoridad y velocidad.

No sustituye la escucha humana: un WER alto marca lineas a revisar o a grabar con actores.

Uso:  python tools/voces/auditar_voces.py [--modelo RUTA_MODELO_VOSK] [--out game/voice/v2]
Salida: tools/voces/auditoria_voces.csv (peor primero) y resumen por personaje en consola.
"""
import argparse
import csv
import json
import os
import re
import unicodedata

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from vosk import KaldiRecognizer, Model, SetLogLevel

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
MODELO_DEFECTO = os.path.expanduser(r"~\Downloads\vosk-model-small-es-0.42")


def limpiar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zñ0-9 ]+", " ", texto).split()


def wer(referencia, hipotesis):
    r, h = referencia, hipotesis
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev = cur
    return d[len(h)] / max(1, len(r))


def palabras_perdidas(referencia, hipotesis):
    restantes = list(hipotesis)
    perdidas = []
    for p in referencia:
        if p in restantes:
            restantes.remove(p)
        else:
            perdidas.append(p)
    return perdidas


def senal(audio, sr):
    mono = audio.mean(axis=1) if audio.ndim > 1 else audio
    pico = float(np.max(np.abs(mono))) if mono.size else 0.0
    ventana = int(sr * 0.02)
    marcos = mono[: len(mono) // ventana * ventana].reshape(-1, ventana)
    rms = np.sqrt((marcos ** 2).mean(axis=1) + 1e-12)
    activo = rms > (rms.max() * 0.03 if rms.size else 0)
    silencio_max = racha = 0
    for a in activo:
        racha = 0 if a else racha + 1
        silencio_max = max(silencio_max, racha)
    saturadas = int(np.sum(np.abs(mono) > 0.999))
    rms_dbfs = 20 * np.log10(np.sqrt(np.mean(mono ** 2)) + 1e-12)
    return mono, {"pico_dbfs": round(20 * np.log10(pico + 1e-12), 1), "rms_dbfs": round(rms_dbfs, 1),
                  "silencio_interno_s": round(silencio_max * 0.02, 2), "muestras_saturadas": saturadas,
                  "duracion_s": round(len(mono) / sr, 2)}


def transcribir(modelo, mono, sr):
    pcm = resample_poly(mono, 16000, sr) if sr != 16000 else mono
    pcm16 = (np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes()
    rec = KaldiRecognizer(modelo, 16000)
    rec.AcceptWaveform(pcm16)
    return json.loads(rec.FinalResult()).get("text", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default=MODELO_DEFECTO)
    ap.add_argument("--out", default=os.path.join(RAIZ, "game", "voice", "v2"))
    ap.add_argument("--inventario", default=os.path.join(AQUI, "inventario_voces.csv"))
    args = ap.parse_args()
    SetLogLevel(-1)
    modelo = Model(args.modelo)

    filas = []
    with open(args.inventario, encoding="utf-8-sig") as f:
        for linea in csv.DictReader(f):
            if linea["voiced"] != "si" and linea["voiced"] != "yes" and linea["voiced"] != "sí":
                continue
            ruta = os.path.join(args.out, linea["Identifier"] + ".ogg")
            if not os.path.exists(ruta):
                filas.append({"id": linea["Identifier"], "personaje": linea["Character"], "problema": "falta archivo"})
                continue
            audio, sr = sf.read(ruta, dtype="float32")
            mono, met = senal(audio, sr)
            ref = limpiar(linea["normalized_text"])
            hip = limpiar(transcribir(modelo, mono, sr))
            met.update({"id": linea["Identifier"], "personaje": linea["Character"], "emocion": linea["emotion"],
                        "wer": round(wer(ref, hip), 3), "perdidas": " ".join(palabras_perdidas(ref, hip)),
                        "palabras_por_s": round(len(ref) / max(0.1, met["duracion_s"]), 2),
                        "texto": linea["normalized_text"], "transcripcion": " ".join(hip)})
            filas.append(met)

    filas.sort(key=lambda r: -r.get("wer", 9))
    salida = os.path.join(AQUI, "auditoria_voces.csv")
    campos = ["id", "personaje", "emocion", "wer", "perdidas", "palabras_por_s", "duracion_s", "silencio_interno_s",
              "pico_dbfs", "rms_dbfs", "muestras_saturadas", "texto", "transcripcion", "problema"]
    with open(salida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)

    print("%-4s %4s %8s %8s %10s %10s %8s %6s" % ("pers", "n", "WER med", "WER p90", "pal/s med", "rms med", "silen>1s", "satur"))
    for p in sorted({r["personaje"] for r in filas}):
        g = [r for r in filas if r["personaje"] == p and "wer" in r]
        if not g:
            continue
        w_ = sorted(r["wer"] for r in g)
        print("%-4s %4d %8.2f %8.2f %10.2f %10.1f %8d %6d" % (
            p, len(g), np.median(w_), w_[int(len(w_) * 0.9) - 1 if len(w_) > 1 else 0],
            np.median([r["palabras_por_s"] for r in g]), np.median([r["rms_dbfs"] for r in g]),
            sum(1 for r in g if r["silencio_interno_s"] > 1.0), sum(r["muestras_saturadas"] for r in g)))
    perdidas = {}
    for r in filas:
        for palabra in r.get("perdidas", "").split():
            perdidas[palabra] = perdidas.get(palabra, 0) + 1
    print("\nPalabras que el reconocedor no oye con mas frecuencia:")
    print(", ".join("%s(%d)" % kv for kv in sorted(perdidas.items(), key=lambda kv: -kv[1])[:40]))
    print("\nDetalle:", salida)


if __name__ == "__main__":
    main()
