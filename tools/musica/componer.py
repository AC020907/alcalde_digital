"""Entry point: python tools/musica/componer.py [--only name] [--seed 7] [--no-spectro]"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import soundfile as sf
from scipy import signal

import dsp
import sfx
import tracks
from catalogo import MUSIC, MUSIC_DIR, SFX, SFX_DIR, SPEC_DIR

CEILING = 0.80  # about -1.9 dBFS; leaves room for Vorbis overshoot below -1 dBFS true peak
THRESH = 0.55


def soft_limit(x):
    a = np.abs(x)
    over = np.maximum(a - THRESH, 0)
    return np.sign(x) * np.where(a > THRESH, THRESH + (CEILING - THRESH) * np.tanh(over / (CEILING - THRESH)), a)


LP_HZ = {"crisis": 8500}


def master(out, target, lp_hz=11000):
    """out: (2, N) periodic signal. Filters are applied circularly so the loop seam stays continuous."""
    hp35 = signal.butter(4, 36, "high", fs=dsp.SR, output="sos")
    lp11 = signal.butter(2, lp_hz, "low", fs=dsp.SR, output="sos")
    out = dsp.circular_filter(out, hp35)
    out = dsp.circular_filter(out, lp11)
    out = out - out.mean(axis=1, keepdims=True)
    x = out.T
    gain = 10 ** ((target - dsp.lufs(x)) / 20)
    for _ in range(5):
        y = soft_limit(x * gain)
        err = target - dsp.lufs(y)
        if abs(err) < 0.15:
            break
        gain *= 10 ** (err / 20)
    return y.astype(np.float32)


def write_ogg(path, data, quality=0.45):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sf.SoundFile(str(path), "w", samplerate=dsp.SR, channels=2, format="OGG", subtype="VORBIS",
                      compression_level=1.0 - quality) as f:
        for i in range(0, len(data), 8192):
            f.write(data[i:i + 8192])


def spectrogram(name, ogg_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x, sr = sf.read(str(ogg_path))
    mono = x.mean(axis=1)
    fig, ax = plt.subplots(figsize=(11, 3.2), dpi=90)
    ax.specgram(mono, NFFT=2048, Fs=sr, noverlap=1536, cmap="magma", vmin=-120, vmax=-30)
    ax.set_ylim(0, 12000)
    ax.set_title(name)
    ax.set_xlabel("s")
    ax.set_ylabel("Hz")
    fig.tight_layout()
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(SPEC_DIR / f"{name}.png")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="render a single track or sfx name")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no-spectro", action="store_true")
    args = ap.parse_args()
    names = list(MUSIC)
    for i, name in enumerate(names):
        if args.only and args.only != name:
            continue
        t0 = time.time()
        song = tracks.BUILDERS[name](args.seed, i)
        out = master(song.render(), MUSIC[name][2], LP_HZ.get(name, 11000))
        path = MUSIC_DIR / f"{name}.ogg"
        write_ogg(path, out)
        if not args.no_spectro:
            spectrogram(name, path)
        print(f"{name:16s} {len(out) / dsp.SR:6.1f}s {path.stat().st_size / 1e6:5.2f} MB  peak {dsp.true_peak_db(out):6.2f} dB  "
              f"LUFS {dsp.lufs(out):6.2f}  ({time.time() - t0:.0f}s)", flush=True)
    for name in SFX:
        if args.only and args.only != name:
            continue
        data = sfx.render(name, args.seed)
        path = SFX_DIR / f"{name}.ogg"
        write_ogg(path, data)
        print(f"{name:16s} {len(data) / dsp.SR:6.2f}s {path.stat().st_size / 1e3:6.1f} kB", flush=True)


if __name__ == "__main__":
    main()
