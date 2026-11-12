"""Audio post-processing: trim, filters, character tone, NOVA FX, loudness, limiter, encode."""
from fractions import Fraction

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, resample_poly, sosfiltfilt

import perfiles as P


def _sos(kind, freq, sr, order=2):
    return butter(order, freq, kind, fs=sr, output="sos")


def shift_pitch(x, factor):
    if abs(factor - 1.0) < 1e-3:
        return x
    frac = Fraction(1.0 / factor).limit_denominator(100)
    return resample_poly(x, frac.numerator, frac.denominator)


def trim_silence(x, sr, pad_ms):
    frame = max(1, int(sr * 0.01))
    n = len(x) // frame
    if n == 0:
        return None
    rms = np.sqrt((x[: n * frame].reshape(n, frame) ** 2).mean(axis=1))
    thr = max(10 ** (-55 / 20), rms.max() * 10 ** (-40 / 20))
    idx = np.where(rms > thr)[0]
    if len(idx) == 0 or rms.max() < 10 ** (-50 / 20):
        return None
    pad = int(sr * pad_ms / 1000)
    start = max(0, idx[0] * frame - pad)
    end = min(len(x), (idx[-1] + 1) * frame + pad)
    return x[start:end]


def compress_pauses(x, sr, max_ms):
    """OneCore cierra cada bloque de prosodia con una pausa larga (~1 s): se acortan los silencios
    internos a un maximo natural, cortando en el centro del hueco con un cruce de 10 ms."""
    frame = max(1, int(sr * 0.01))
    n = len(x) // frame
    if n == 0:
        return x
    rms = np.sqrt((x[: n * frame].reshape(n, frame) ** 2).mean(axis=1))
    silent = rms < max(10 ** (-55 / 20), rms.max() * 10 ** (-38 / 20))
    keep = int(max_ms / 10)
    out, cursor, i = [], 0, 0
    fade = frame
    while i < n:
        if not silent[i]:
            i += 1
            continue
        j = i
        while j < n and silent[j]:
            j += 1
        if j < n and j - i > keep:
            cut_from = (i + keep // 2) * frame
            cut_to = (j - (keep - keep // 2)) * frame
            head = x[cursor:cut_from].copy()
            tail_start = cut_to
            if len(head) > fade:
                ramp = np.linspace(1.0, 0.0, fade)
                head[-fade:] = head[-fade:] * ramp + x[tail_start - fade:tail_start] * (1 - ramp)
            out.append(head)
            cursor = tail_start
        i = j
    out.append(x[cursor:])
    return np.concatenate(out) if len(out) > 1 else x


def clean_voice(x, sr, tone_db=0.0, drive=0.0):
    x = sosfiltfilt(_sos("highpass", 80, sr), x)
    band = sosfiltfilt(_sos("bandpass", [4500, 7200], sr, 4), x)
    env = uniform_filter1d(np.abs(band), max(1, int(sr * 0.005)))
    ref = np.sqrt(np.mean(x ** 2)) + 1e-9
    gain = np.minimum(1.0, (0.30 * ref) / (env + 1e-9))
    gain = uniform_filter1d(gain, max(1, int(sr * 0.003)))
    x = x - 0.7 * (1.0 - gain) * band
    x = sosfiltfilt(_sos("lowpass", 7000, sr), x)
    if tone_db:
        hp = sosfiltfilt(_sos("highpass", 3000, sr), x)
        x = x + (10 ** (tone_db / 20) - 1.0) * hp
    if drive > 0:
        peak = np.max(np.abs(x)) + 1e-9
        x = np.tanh(drive * x / peak) / np.tanh(drive) * peak
    return x


def _frac_delay(x, delay_samples):
    idx = np.arange(len(x)) - delay_samples
    return np.interp(idx, np.arange(len(x)), x, left=0.0, right=0.0)


def nova_fx(x, sr, cfg):
    n = len(x)
    t = np.arange(n) / sr
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    ring = np.sin(2 * np.pi * cfg["ring_hz"] * t)
    x = x * (1 - cfg["ring_mix"]) + cfg["ring_mix"] * x * ring
    step = sr / cfg["crush_hz"]
    held = x[(np.floor(np.arange(n) / step) * step).astype(int).clip(0, n - 1)]
    levels = 2 ** (cfg["crush_bits"] - 1)
    x = np.round(held * levels) / levels
    d = cfg["comb_ms"] * sr / 1000
    x = (x + cfg["comb_gain"] * _frac_delay(x, d)) / (1 + cfg["comb_gain"])
    chans = []
    for phase in (0.0, np.pi):
        lfo = np.sin(2 * np.pi * 0.35 * t + phase)
        delayed = np.interp(np.arange(n) - (12e-3 + 1.5e-3 * lfo) * sr, np.arange(n), x, left=0.0, right=0.0)
        mix = cfg["chorus_mix"]
        chans.append(x * (1 - mix) + delayed * mix)
    left = chans[0]
    right = _frac_delay(chans[1], cfg["stereo_delay_ms"] * sr / 1000)
    return np.stack([left, right], axis=1)


def measure_lufs(x, sr):
    y = x
    if y.shape[0] / sr < 0.5:
        reps = int(np.ceil(0.5 * sr / y.shape[0])) + 1
        y = np.tile(y, (reps, 1) if y.ndim == 2 else reps)
    try:
        v = pyln.Meter(sr).integrated_loudness(y)
    except Exception:
        v = float("-inf")
    if not np.isfinite(v):
        rms = np.sqrt(np.mean(np.asarray(y) ** 2)) + 1e-12
        v = 20 * np.log10(rms) - 0.7
    return float(v)


def true_peak_db(x):
    up = resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(up)) + 1e-12))


def limit(x, sr, ceiling_db):
    ceiling = 10 ** (ceiling_db / 20)
    env = np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)
    target = np.minimum(1.0, ceiling / (env + 1e-12))
    win = max(1, int(sr * 0.005))
    g = minimum_filter1d(target, 2 * win + 1)
    g = uniform_filter1d(g, win)
    g = np.minimum(g, target) if win == 1 else g
    return x * (g[:, None] if x.ndim == 2 else g)


def fades(x, sr, ms):
    n = min(int(sr * ms / 1000), len(x) // 2)
    if n <= 0:
        return x
    ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))
    ramp = ramp[:, None] if x.ndim == 2 else ramp
    x = x.copy()
    x[:n] *= ramp
    x[-n:] *= ramp[::-1]
    return x


def process(raw, sr, prof, loud_db, suspensivos=False):
    """raw: mono float TTS output at sr. Returns (audio float32 at OUTPUT_SAMPLE_RATE, stats) or None if silent."""
    x = shift_pitch(raw, prof.get("shift", 1.0))
    x = trim_silence(x, sr, P.PAD_MS)
    if x is None:
        return None
    x = compress_pauses(x, sr, prof.get("max_pause_ms", 450) + (300 if suspensivos else 0))
    x = clean_voice(x, sr, prof.get("tone_db", 0.0), prof.get("drive", 0.0))
    if prof.get("nova_fx"):
        x = nova_fx(x, sr, prof["nova_fx"])
    out_sr = P.OUTPUT_SAMPLE_RATE
    x = resample_poly(x, out_sr * 1, sr * 1, axis=0) if sr != out_sr else x
    target = P.TARGET_LUFS + prof.get("loudness_offset_db", 0.0) + loud_db
    measured = measure_lufs(x, out_sr)
    gain_db = float(np.clip(target - measured, -20, 30))
    x = x * 10 ** (gain_db / 20)
    pre_limit = true_peak_db(x)
    x = limit(x, out_sr, P.TRUE_PEAK_CEILING_DB - 0.7)
    tp = true_peak_db(x)
    if tp > P.TRUE_PEAK_CEILING_DB - 0.3:
        x = x * 10 ** ((P.TRUE_PEAK_CEILING_DB - 0.3 - tp) / 20)
    x = fades(x, out_sr, P.FADE_MS)
    stats = {
        "lufs": round(measure_lufs(x, out_sr), 2),
        "tp_db": round(true_peak_db(x), 2),
        "limited_db": round(max(0.0, pre_limit - P.TRUE_PEAK_CEILING_DB), 2),
        "dur": round(len(x) / out_sr, 3),
    }
    return x.astype(np.float32), out_sr, stats


def write_ogg(path, audio, sr):
    ch = 1 if audio.ndim == 1 else audio.shape[1]
    with sf.SoundFile(path, "w", sr, ch, format="OGG", subtype="VORBIS",
                      compression_level=P.VORBIS_COMPRESSION_LEVEL) as f:
        f.write(audio)


def write_ogg_checked(path, audio, sr, ceiling_db):
    """Encode, decode back and lower the gain until the decoded true peak respects the ceiling (Vorbis overshoots)."""
    for _ in range(4):
        write_ogg(path, audio, sr)
        decoded, _sr = sf.read(path, dtype="float64")
        tp = true_peak_db(decoded)
        if tp <= ceiling_db:
            break
        audio = (audio * 10 ** ((ceiling_db - tp - 0.1) / 20)).astype(np.float32)
    return decoded, tp
