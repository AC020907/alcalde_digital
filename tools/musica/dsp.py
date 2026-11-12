"""Core DSP helpers: envelopes, filters, reverb, loudness metering."""
from functools import lru_cache

import numpy as np
from scipy import signal

SR = 44100
_rng = np.random.default_rng(0)


def set_rng(seed):
    global _rng
    _rng = np.random.default_rng(seed)


def rng():
    return _rng


def tarr(n):
    return np.arange(n) / SR


def noise(n):
    return _rng.standard_normal(n)


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def adsr(dur, a=0.01, d=0.2, s=0.7, r=0.3):
    """Gate envelope; output length is dur + r so the release tail is included."""
    ng = max(1, int(dur * SR))
    nr = int(r * SR)
    t = np.arange(ng) / SR
    att = np.sin(np.clip(t / max(a, 1e-4), 0, 1) * np.pi / 2) ** 2
    dec = s + (1 - s) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    g = att * dec
    rel = g[-1] * 0.5 * (1 + np.cos(np.pi * np.arange(nr) / max(nr, 1)))
    return np.concatenate([g, rel])


def fade(x, fin=0.002, fout=0.01):
    x = np.array(x, dtype=float)
    n = x.shape[-1]
    a = min(int(fin * SR), n // 2)
    b = min(int(fout * SR), n // 2)
    if a > 0:
        x[..., :a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if b > 0:
        x[..., n - b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return x


@lru_cache(maxsize=None)
def _sos(kind, lo, hi, order):
    if kind == "bp":
        return signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    if kind == "lp":
        return signal.butter(order, hi, btype="low", fs=SR, output="sos")
    return signal.butter(order, lo, btype="high", fs=SR, output="sos")


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bp", lo, hi, order), x, axis=-1)


def lp(x, hi, order=2):
    return signal.sosfilt(_sos("lp", 0, hi, order), x, axis=-1)


def hp(x, lo, order=2):
    return signal.sosfilt(_sos("hp", lo, 0, order), x, axis=-1)


def circular_filter(x, sos):
    """Filter a periodic signal without a seam: run on 3 copies, keep the middle."""
    n = x.shape[-1]
    y = signal.sosfilt(sos, np.concatenate([x, x, x], axis=-1), axis=-1)
    return y[..., n:2 * n]


def bitcrush(x, bits=6, hold=1):
    y = np.asarray(x, dtype=float)
    if hold > 1:
        y = np.repeat(y[::hold], hold)[: len(x)]
    q = 2.0 ** (bits - 1)
    return np.round(y * q) / q


def make_ir(rt60, seed, predelay=0.012):
    r = np.random.default_rng(seed)
    n = int(rt60 * 1.15 * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n))
    early = [0.011, 0.019, 0.027, 0.041, 0.053, 0.071, 0.089]
    for c in range(2):
        nz = r.standard_normal(n)
        lo = lp(nz, 2400) * np.exp(-6.91 * t / rt60)
        hi = bp(r.standard_normal(n), 2400, 8000) * np.exp(-6.91 * t / (rt60 * 0.45)) * 0.5
        ir[c] = lo + hi
        ir[c] *= np.minimum(1, t / 0.02) ** 2
        for k, d in enumerate(early):
            i = int((d + c * 0.0017) * SR)
            ir[c, i] += (0.5 / (k + 1)) * (1 if (k + c) % 2 == 0 else -1)
    ir = np.pad(ir, ((0, 0), (int(predelay * SR), 0)))
    ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
    return ir


def reverb(x, ir):
    n = x.shape[-1]
    return np.stack([signal.fftconvolve(x[c], ir[c])[:n] for c in range(2)])


def _k_weight(x):
    fs = SR
    g, q, f0 = 3.999843853973347, 0.7071752369554196, 1681.974450955533
    A = 10 ** (g / 40)
    w0 = 2 * np.pi * f0 / fs
    al = np.sin(w0) / (2 * q)
    c = np.cos(w0)
    sa = 2 * np.sqrt(A) * al
    b = [A * ((A + 1) + (A - 1) * c + sa), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sa)]
    a = [(A + 1) - (A - 1) * c + sa, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sa]
    y = signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)
    f1, q1 = 38.13547087602444, 0.5003270373238773
    w1 = 2 * np.pi * f1 / fs
    al1 = np.sin(w1) / (2 * q1)
    c1 = np.cos(w1)
    b2 = np.array([(1 + c1) / 2, -(1 + c1), (1 + c1) / 2])
    a2 = np.array([1 + al1, -2 * c1, 1 - al1])
    return signal.lfilter(b2 / a2[0], a2 / a2[0], y, axis=0)


def lufs(x):
    """Approximate BS.1770 integrated loudness of an (n, 2) array, with gating."""
    y = _k_weight(np.asarray(x, dtype=float))
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        return -70.0
    p = np.cumsum(np.concatenate([np.zeros((1, y.shape[1])), y ** 2]), axis=0)
    starts = np.arange(0, len(y) - blk + 1, hop)
    z = (p[starts + blk] - p[starts]) / blk
    lk = -0.691 + 10 * np.log10(np.maximum(z.sum(axis=1), 1e-12))
    keep = lk > -70
    if not keep.any():
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(z[keep].sum(axis=1))) - 10
    keep &= lk > rel
    return float(-0.691 + 10 * np.log10(np.mean(z[keep].sum(axis=1))))


def true_peak_db(x):
    up = signal.resample_poly(np.asarray(x, dtype=float), 4, 1, axis=0)
    return float(20 * np.log10(max(np.max(np.abs(up)), 1e-9)))
