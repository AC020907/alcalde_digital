"""One-shot sound effects."""
from functools import partial

import numpy as np

import dsp
import instruments as I
from dsp import SR, bitcrush, bp, fade, lp, hp, noise, tarr
from catalogo import SFX

TWO_PI = 2 * np.pi


def _mix(parts, n=None):
    n = n or max(o + len(p) for o, p in parts)
    y = np.zeros(n)
    for o, p in parts:
        e = min(o + len(p), n)
        y[o:e] += p[: e - o]
    return y


def _at(sec):
    return int(sec * SR)


def _stereo(mono, width=0.0, delay_ms=0.0):
    """Cheap widening: a very short Haas delay on one channel."""
    d = int(delay_ms * SR / 1000)
    r = np.concatenate([np.zeros(d), mono])[: len(mono)] if d else mono
    return np.stack([mono, r * (1 - width) + mono * width])


def _reverb_small(st, rt60=0.5, amount=0.18):
    ir = dsp.make_ir(rt60, 11)
    pad = np.pad(st, ((0, 0), (0, ir.shape[1])))
    return pad + dsp.reverb(pad, ir) * amount


def pista():
    b = partial(I.bell, decay=0.8, kind="glass")
    y = _mix([(0, b(dsp.mtof(79), 0.1, 0.7)), (_at(0.12), b(dsp.mtof(86), 0.1, 0.8))])
    return _reverb_small(_stereo(y, 0.3, 0.6), 0.6, 0.22)


def logro():
    b = partial(I.bell, decay=0.9, kind="glass")
    notes = [84, 88, 91, 96, 100]
    y = _mix([(_at(0.075 * i), b(dsp.mtof(m), 0.05, 0.55 + 0.08 * i)) for i, m in enumerate(notes)])
    y += 0.0
    low = _mix([(0, I.epiano(dsp.mtof(60), 0.4, 0.5) * 0.5)], len(y))
    return _reverb_small(_stereo(y + low, 0.3, 0.8), 0.8, 0.25)


def error():
    n = _at(0.4)
    t = tarr(n)
    thud = np.sin(TWO_PI * np.cumsum(90 + 60 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.09)
    buz = (np.sign(np.sin(TWO_PI * 122 * t)) * 0.0 + np.sin(TWO_PI * 122 * t) + 0.5 * np.sin(TWO_PI * 129 * t) + 0.3 * np.sin(TWO_PI * 244 * t))
    buz = lp(buz, 900) * np.exp(-t / 0.12) * np.minimum(1, t / 0.01)
    y = thud * 0.9 + buz * 0.35
    return _stereo(fade(y, 0.002, 0.08), 0.0, 0)


def decision():
    n = _at(0.3)
    t = tarr(n)
    click = bp(noise(n), 1800, 6000) * np.exp(-t / 0.003) * 0.5
    tone = (np.sin(TWO_PI * 659.3 * t) + 0.3 * np.sin(TWO_PI * 988 * t)) * np.exp(-t / 0.07) * np.minimum(1, t / 0.003)
    return _stereo(fade(click + tone * 0.7, 0.001, 0.08), 0.2, 0.4)


def menu_hover():
    n = _at(0.05)
    t = tarr(n)
    y = np.sin(TWO_PI * 2400 * t) * np.exp(-t / 0.008) * np.minimum(1, t / 0.001)
    return _stereo(fade(y, 0.001, 0.015))


def menu_select():
    n = _at(0.35)
    t = tarr(n)
    a = np.sin(TWO_PI * 523.3 * t) * np.exp(-t / 0.09)
    bb = np.zeros(n)
    k = _at(0.07)
    bb[k:] = (np.sin(TWO_PI * 784 * t[: n - k]) + 0.25 * np.sin(TWO_PI * 1568 * t[: n - k])) * np.exp(-t[: n - k] / 0.1)
    y = (a + bb) * np.minimum(1, t / 0.003)
    return _reverb_small(_stereo(fade(y, 0.001, 0.1), 0.2, 0.5), 0.3, 0.12)


def pagina():
    n = _at(0.5)
    t = tarr(n)
    nz = noise(n)
    sweep = np.zeros(n)
    # sweep the band-pass by crossfading three bands
    b1 = bp(nz, 800, 2500)
    b2 = bp(nz, 2000, 5500)
    b3 = bp(nz, 4000, 9000)
    x = t / t[-1]
    sweep = b1 * np.exp(-((x - 0.2) / 0.2) ** 2) + b2 * np.exp(-((x - 0.5) / 0.2) ** 2) + b3 * np.exp(-((x - 0.8) / 0.2) ** 2) * 0.7
    env = np.sin(np.pi * np.clip(x, 0, 1)) ** 1.5 * (0.6 + 0.4 * np.random.default_rng(3).random(n) ** 0.1)
    crinkle = np.zeros(n)
    r = np.random.default_rng(5)
    for pos in (r.uniform(0.0, 0.45, 9) * SR).astype(int):
        m = int(0.004 * SR)
        crinkle[pos:pos + m] += bp(noise(m), 2500, 9000) * np.exp(-np.arange(m) / (0.0012 * SR)) * r.uniform(0.3, 0.9)
    y = sweep * env * 0.8 + crinkle * 0.5
    st = np.stack([y, np.roll(y, 40)])
    st[0] *= np.linspace(1.0, 0.8, n)
    st[1] *= np.linspace(0.8, 1.0, n)
    return fade(st, 0.01, 0.1)


def glitch():
    n = _at(0.4)
    t = tarr(n)
    base = np.sin(TWO_PI * np.cumsum(300 + 1500 * ((t * 23) % 1.0)) / SR) * 0.5
    base += 0.4 * bp(noise(n), 1500, 8000)
    gate = (np.floor(t * 40) % 3 != 0).astype(float)
    y = bitcrush(base * gate, 4, 4)
    seg = y[_at(0.1):_at(0.14)]
    y[_at(0.2):_at(0.2) + len(seg) * 3] = np.tile(seg, 3)[: n - _at(0.2)]
    y = lp(y, 7000) * np.exp(-t / 0.28)
    stereo = np.stack([y, np.roll(y, _at(0.003))])
    return fade(stereo, 0.003, 0.08)


def transicion():
    n = _at(1.3)
    t = tarr(n)
    x = t / t[-1]
    nz = noise(n)
    out = np.zeros(n)
    bands = [(300, 1200), (900, 3000), (2200, 6500)]
    centers = [0.35, 0.5, 0.62]
    for (lo, hi), c in zip(bands, centers):
        out += bp(nz, lo, hi) * np.exp(-((x - c) / 0.22) ** 2) * (1.0 if hi < 4000 else 0.5)
    out *= np.sin(np.pi * x) ** 1.3
    pan = np.sin(np.pi * x * 0.5)
    st = np.stack([out * np.cos(pan * np.pi / 2) * 1.2, out * np.sin(pan * np.pi / 2) * 1.2])
    return fade(st, 0.03, 0.25)


def voz_blip():
    n = _at(0.05)
    t = tarr(n)
    y = (np.sin(TWO_PI * 330 * t) + 0.3 * np.sin(TWO_PI * 660 * t)) * np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 1.2
    return _stereo(fade(y, 0.002, 0.012))


BUILDERS = {
    "pista": pista, "logro": logro, "error": error, "decision": decision, "menu_hover": menu_hover,
    "menu_select": menu_select, "pagina": pagina, "glitch": glitch, "transicion": transicion, "voz_blip": voz_blip,
}


def render(name, seed=7):
    dsp.set_rng(seed * 77 + sorted(SFX).index(name))
    st = BUILDERS[name]()
    st = fade(st, 0.002, 0.02)
    peak = SFX[name][2]
    st = st / np.max(np.abs(st)) * 10 ** (peak / 20.0)
    return st.T.astype(np.float32)
