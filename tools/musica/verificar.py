"""Decode every generated file and check duration, format, peak, loudness, DC and loop seams."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import soundfile as sf

import dsp
from catalogo import MUSIC, MUSIC_DIR, SFX, SFX_DIR

PEAK_MUSIC = -1.0
PEAK_SFX = -3.0
LUFS_TOL = 1.0
DC_MAX = 0.002
HF_MAX_DB = -25.0
LF_MAX_DB = -30.0
STEP_RATIO_MAX = 1.5
SEAM_HF_MAX_DB = 3.0


def band_db(mono, lo, hi):
    spec = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))) ** 2
    f = np.fft.rfftfreq(len(mono), 1 / dsp.SR)
    tot = spec.sum() + 1e-18
    return 10 * np.log10(spec[(f >= lo) & (f < hi)].sum() / tot + 1e-18)


def frame_hf(mono, size=2048, hop=1024, lo=6000):
    win = np.hanning(size)
    f = np.fft.rfftfreq(size, 1 / dsp.SR)
    idx = f >= lo
    n = (len(mono) - size) // hop
    frames = np.stack([mono[i * hop:i * hop + size] * win for i in range(n)])
    return (np.abs(np.fft.rfft(frames, axis=1)) ** 2)[:, idx].sum(axis=1)


def loop_metrics(x):
    """Returns (step_ratio, seam_hf_over_p99_db)."""
    ratios = []
    for c in range(x.shape[1]):
        d = np.abs(np.diff(x[:, c]))
        ref = max(np.percentile(d, 99.9), 1e-6)
        ratios.append(abs(x[0, c] - x[-1, c]) / ref)
    mono = x.mean(axis=1)
    hf = frame_hf(mono)
    wrap = np.concatenate([mono[-1024:], mono[:1024]])
    joint = (np.abs(np.fft.rfft(wrap * np.hanning(2048))) ** 2)[np.fft.rfftfreq(2048, 1 / dsp.SR) >= 6000].sum()
    seam_db = 10 * np.log10((joint + 1e-18) / (np.percentile(hf, 99) + 1e-18))
    return max(ratios), seam_db


def check(kind, name, path, spec):
    fails = []
    row = {"name": name}
    try:
        x, sr = sf.read(str(path), dtype="float64", always_2d=True)
    except Exception as e:
        return {"name": name}, [f"decode error: {e}"]
    dur = len(x) / sr
    row.update(dur=dur, size=path.stat().st_size / 1024)
    if sr != 44100:
        fails.append(f"sr {sr}")
    if x.shape[1] != 2:
        fails.append(f"channels {x.shape[1]}")
    if not (spec[0] <= dur <= spec[1]):
        fails.append(f"duration {dur:.1f}s outside {spec[0]}-{spec[1]}")
    tp = dsp.true_peak_db(x)
    row["tp"] = tp
    limit = PEAK_MUSIC if kind == "music" else PEAK_SFX
    if tp > limit:
        fails.append(f"true peak {tp:.2f} > {limit}")
    dc = float(np.max(np.abs(x.mean(axis=0))))
    row["dc"] = dc
    if dc > DC_MAX:
        fails.append(f"DC {dc:.4f}")
    if kind == "music":
        l = dsp.lufs(x)
        row["lufs"] = l
        if abs(l - spec[2]) > LUFS_TOL:
            fails.append(f"LUFS {l:.1f} vs target {spec[2]}")
        mono = x.mean(axis=1)
        hf = band_db(mono, 10000, 22050)
        lf = band_db(mono, 0, 28)
        row.update(hf=hf, lf=lf)
        if hf > HF_MAX_DB:
            fails.append(f"HF>10k {hf:.1f} dB")
        if lf > LF_MAX_DB:
            fails.append(f"LF<28Hz {lf:.1f} dB")
        step, seam = loop_metrics(x)
        row.update(step=step, seam=seam)
        if step > STEP_RATIO_MAX:
            fails.append(f"loop step x{step:.1f}")
        if seam > SEAM_HF_MAX_DB:
            fails.append(f"loop seam HF +{seam:.1f} dB")
    else:
        row["edge"] = float(max(abs(x[0]).max(), abs(x[-1]).max()))
        if row["edge"] > 0.01:
            fails.append(f"edge sample {row['edge']:.4f}")
        if np.max(np.abs(x)) < 0.05:
            fails.append("too quiet")
    return row, fails


def main():
    bad = 0
    print("MUSIC")
    print(f"{'name':16s}{'dur s':>7s}{'KB':>7s}{'TP dB':>8s}{'LUFS':>7s}{'DC':>8s}{'>10k':>7s}{"<28":>6s}{'step':>6s}{'seam':>7s}  status")
    for name, spec in MUSIC.items():
        p = MUSIC_DIR / f"{name}.ogg"
        if not p.exists():
            print(f"{name:16s} MISSING")
            bad += 1
            continue
        r, f = check("music", name, p, spec)
        if "dur" in r and "seam" in r:
            print(f"{name:16s}{r['dur']:7.1f}{r['size']:7.0f}{r['tp']:8.2f}{r['lufs']:7.2f}{r['dc']:8.5f}{r['hf']:7.1f}"
                  f"{r['lf']:6.1f}{r['step']:6.2f}{r['seam']:7.1f}  {'OK' if not f else 'FAIL: ' + '; '.join(f)}")
        else:
            print(f"{name:16s} FAIL: {'; '.join(f)}")
        bad += bool(f)
    print("\nSFX")
    print(f"{'name':16s}{'dur s':>7s}{'KB':>7s}{'TP dB':>8s}{'DC':>8s}{'edge':>8s}  status")
    for name, spec in SFX.items():
        p = SFX_DIR / f"{name}.ogg"
        if not p.exists():
            print(f"{name:16s} MISSING")
            bad += 1
            continue
        r, f = check("sfx", name, p, spec)
        if "dur" in r and "edge" in r:
            print(f"{name:16s}{r['dur']:7.2f}{r['size']:7.1f}{r['tp']:8.2f}{r['dc']:8.5f}{r['edge']:8.4f}  {'OK' if not f else 'FAIL: ' + '; '.join(f)}")
        else:
            print(f"{name:16s} FAIL: {'; '.join(f)}")
        bad += bool(f)
    total = sum(p.stat().st_size for n in MUSIC if (p := MUSIC_DIR / f"{n}.ogg").exists())
    print(f"\nTotal music size: {total / 1e6:.2f} MB")
    print("RESULT:", "ALL OK" if not bad else f"{bad} file(s) FAILED")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
