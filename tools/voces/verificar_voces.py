"""Numeric verification of generated voice files against the inventory.

Usage: python tools/voces/verificar_voces.py --out tools/voces/muestras [--inventario tools/voces/inventario_voces.csv]
Checks: file exists, decodes, duration plausible vs text length, loudness and true peak in range, not silent.
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import perfiles as P  # noqa: E402
import procesado  # noqa: E402


def median_f0(x, sr):
    x = x - x.mean()
    fr = int(sr * 0.04)
    vals = []
    for i in range(0, len(x) - fr, fr // 2):
        seg = x[i:i + fr]
        if np.sqrt((seg ** 2).mean()) < 0.02:
            continue
        ac = np.correlate(seg, seg, "full")[fr - 1:]
        lo, hi = int(sr / 400), int(sr / 70)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.5 * ac[0]:
            vals.append(sr / k)
    return float(np.median(vals)) if vals else 0.0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--inventario", type=Path, default=HERE / "inventario_voces.csv")
    args = ap.parse_args()

    with open(args.inventario, encoding="utf-8-sig", newline="") as f:
        inv = list(csv.DictReader(f))
    voiced = [r for r in inv if r["voiced"] == "yes"]
    expected = {r["Identifier"] for r in voiced}
    on_disk = {p.stem for p in args.out.glob("*.ogg")}

    problems = []
    for oid in sorted(expected - on_disk):
        problems.append((oid, "archivo faltante"))
    for oid in sorted(on_disk - expected):
        problems.append((oid, "archivo huerfano (sin linea con voz)"))

    per_char = {}
    total_bytes = 0
    for r in voiced:
        oid = r["Identifier"]
        p = args.out / f"{oid}.ogg"
        if not p.exists():
            continue
        total_bytes += p.stat().st_size
        try:
            data, sr = sf.read(p, dtype="float64")
        except Exception as e:
            problems.append((oid, f"no decodifica: {e}"))
            continue
        dur = len(data) / sr
        mono = data if data.ndim == 1 else data.mean(axis=1)
        cps = len(r["normalized_text"]) / max(dur - 0.12, 0.05)
        lufs = procesado.measure_lufs(data, sr)
        tp = procesado.true_peak_db(data)
        rms_db = 20 * np.log10(np.sqrt(np.mean(mono ** 2)) + 1e-12)
        d = per_char.setdefault(r["Character"], {"lufs": [], "tp": [], "dur": [], "cps": [], "f0": [], "n": 0})
        d["n"] += 1
        d["lufs"].append(lufs)
        d["tp"].append(tp)
        d["dur"].append(dur)
        d["cps"].append(cps)
        d["f0"].append(median_f0(mono, sr))
        if dur < 0.3:
            problems.append((oid, f"duracion {dur:.2f}s demasiado corta"))
        if not (5.0 <= cps <= 30.0):
            problems.append((oid, f"velocidad implausible {cps:.1f} car/s (dur {dur:.2f}s)"))
        if rms_db < -40:
            problems.append((oid, f"casi silencioso (rms {rms_db:.1f} dB)"))
        if tp > P.TRUE_PEAK_CEILING_DB + 0.05:
            problems.append((oid, f"true peak {tp:.2f} dBTP > {P.TRUE_PEAK_CEILING_DB}"))
        if abs(lufs - P.TARGET_LUFS) > 3.5:
            problems.append((oid, f"loudness {lufs:.1f} LUFS fuera de {P.TARGET_LUFS}+-3.5"))

    print(f"Esperados: {len(expected)}  en disco: {len(on_disk)}  tamano total: {total_bytes / 1024:.0f} KiB")
    print(f"{'char':5}{'n':>4}{'LUFS med':>10}{'LUFS min/max':>16}{'TP max':>8}{'dur med':>9}{'car/s med':>10}{'F0 med Hz':>10}")
    for c, d in sorted(per_char.items()):
        print(f"{c:5}{d['n']:>4}{np.median(d['lufs']):>10.1f}{min(d['lufs']):>8.1f}/{max(d['lufs']):<7.1f}"
              f"{max(d['tp']):>8.2f}{np.median(d['dur']):>9.2f}{np.median(d['cps']):>10.1f}"
              f"{np.median([v for v in d['f0'] if v]):>10.0f}")
    print(f"Problemas: {len(problems)}")
    for oid, msg in problems:
        print(f"  {oid}: {msg}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
