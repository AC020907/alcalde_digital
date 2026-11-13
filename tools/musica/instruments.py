"""Soft, band-limited voices and percussion. All return mono arrays except pad/strings (stereo)."""
import numpy as np

from dsp import SR, adsr, bp, bitcrush, fade, hp, lp, noise, rng, tarr

TWO_PI = 2 * np.pi
MAX_F = 10500.0


def _partials(f, t, ratios, amps, rates, phase0=0.0):
    y = np.zeros_like(t)
    for r, a, lam in zip(ratios, amps, rates):
        fk = f * r
        if fk > MAX_F:
            continue
        y += a * np.exp(-lam * t) * np.sin(TWO_PI * fk * t + phase0)
    return y


def _ring(dur, tail):
    n = int((dur + tail) * SR)
    return n, tarr(n)


def _end_fade(y, ms=60):
    return fade(y, 0.0015, ms / 1000.0)


def epiano(f, dur, vel=0.8):
    gate = adsr(dur, 0.004, 1.0, 1.0, 0.3)
    n = len(gate)
    t = tarr(n)
    tau = float(np.clip(1.8 * (261.0 / f) ** 0.5, 0.5, 3.2))
    idx = vel * (0.9 * np.exp(-t / 0.3) + 0.3)
    y = np.sin(TWO_PI * f * t + idx * np.sin(TWO_PI * f * t))
    if f * 7 < MAX_F:
        y += 0.10 * vel * np.exp(-t / 0.035) * np.sin(TWO_PI * f * 7 * t)
    y *= np.exp(-t / tau) * gate
    return y * (0.35 + 0.65 * vel) * 0.8


def piano(f, dur, vel=0.7):
    gate = adsr(dur, 0.003, 1.0, 1.0, 0.28)
    n = len(gate)
    t = tarr(n)
    tau = float(np.clip(4.2 * (261.0 / f) ** 0.7, 0.7, 8.0))
    k = np.arange(1, 13)
    inh = 0.00025 * (f / 261.0) ** 1.5
    ratios = k * np.sqrt(1 + inh * k * k)
    amps = k ** -1.05 * (0.45 + 0.55 * vel) ** ((k - 1) * 0.55)
    rates = (1 / tau) * (1 + 0.55 * (k - 1))
    y = _partials(f, t, ratios, amps, rates) + _partials(f * 1.0004, t, ratios, amps, rates)
    return y * gate * 0.28 * (0.4 + 0.6 * vel)


def bell(f, dur, vel=0.7, decay=2.2, kind="warm"):
    if kind == "glass":
        ratios, amps = [1, 2.76, 5.4, 8.93], [1, 0.4, 0.18, 0.08]
    else:
        ratios, amps = [1, 2.0, 3.0, 4.16, 5.43], [1, 0.38, 0.16, 0.08, 0.04]
    n, t = _ring(dur, decay * 1.2)
    rates = [(1.0 / decay) * (1 + 0.9 * i) for i in range(len(ratios))]
    y = _partials(f, t, ratios, amps, rates)
    y *= np.minimum(1, t / 0.002)
    return _end_fade(y, 120) * vel * 0.5


def musicbox(f, dur, vel=0.7, detune_cents=0.0):
    f = f * 2 ** (detune_cents / 1200.0)
    n, t = _ring(dur, 2.0)
    ratios, amps = [1, 2.01, 3.97, 5.98], [1, 0.45, 0.2, 0.1]
    rates = [1.8 * (1 + 0.7 * i) for i in range(4)]
    y = _partials(f, t, ratios, amps, rates)
    y *= np.minimum(1, t / 0.0015)
    return _end_fade(y, 100) * vel * 0.45


def pluck(f, dur, vel=0.7, tau=0.35, bright=0.6, nh=8):
    gate = adsr(dur, 0.002, 1.0, 1.0, 0.12)
    n = len(gate)
    t = tarr(n)
    k = np.arange(1, nh + 1)
    amps = (1.0 / k) ** 1.2 * bright ** (k - 1)
    rates = (1 / tau) * (1 + 0.9 * (k - 1))
    y = _partials(f, t, k, amps, rates)
    return y * gate * 0.55 * (0.4 + 0.6 * vel)


def marimba(f, dur, vel=0.7):
    n, t = _ring(dur, 0.8)
    y = _partials(f, t, [1, 4.0, 10.0], [1, 0.25, 0.06], [5.5, 18.0, 40.0])
    y *= np.minimum(1, t / 0.002)
    return _end_fade(y, 60) * vel * 0.7


def bass(f, dur, vel=0.8, warmth=1.4):
    gate = adsr(dur, 0.012, 0.25, 0.6, 0.14)
    n = len(gate)
    t = tarr(n)
    y = np.sin(TWO_PI * f * t) + 0.38 * np.sin(2 * TWO_PI * f * t) + 0.14 * np.sin(3 * TWO_PI * f * t)
    y = np.tanh(warmth * y * 0.8) / np.tanh(warmth * 0.8)
    return y * gate * vel * 0.6


def stab(f, dur, vel=0.8, tau=0.18):
    gate = adsr(dur, 0.004, 1.0, 1.0, 0.08)
    n = len(gate)
    t = tarr(n)
    k = np.arange(1, 11)
    y = _partials(f, t, k, 1.0 / k, 1 / tau * (0.4 + 0.5 * k))
    y += _partials(f * 1.003, t, k, 0.7 / k, 1 / tau * (0.4 + 0.5 * k))
    return y * gate * vel * 0.28


def pad(f, dur, vel=0.7, bright=0.5, att=0.8, rel=1.6, tremolo=0.0, trem_rate=5.4, detune=7.0, voices=3):
    env = adsr(dur, att, 1.0, 1.0, rel)
    n = len(env)
    t = tarr(n)
    ks = np.arange(1, 8)
    amps = (1.0 / ks) ** (2.4 - 1.5 * bright)
    amps = amps / amps.sum()
    out = np.zeros((2, n))
    r = rng()
    offs = np.linspace(-detune, detune, voices)
    pans = np.linspace(-0.7, 0.7, voices)
    for d, pn in zip(offs, pans):
        fd = f * 2 ** (d / 1200.0)
        vr = r.uniform(0.2, 0.45)
        beta = f * 0.0018 / vr
        ph = TWO_PI * fd * t + beta * np.sin(TWO_PI * vr * t + r.uniform(0, TWO_PI))
        y = np.zeros(n)
        for k, a in zip(ks, amps):
            if fd * k < MAX_F:
                y += a * np.sin(k * ph)
        ang = (pn + 1) * np.pi / 4
        out[0] += y * np.cos(ang)
        out[1] += y * np.sin(ang)
    out *= env / voices * 1.3
    if tremolo > 0:
        lfo = 1 - tremolo * (0.5 + 0.5 * np.sin(TWO_PI * trem_rate * t + r.uniform(0, TWO_PI)))
        out *= lfo
    return out * vel * 0.6


def strings(f, dur, vel=0.7, tremolo=0.0):
    return pad(f, dur, vel, bright=0.85, att=0.45, rel=1.2, tremolo=tremolo, detune=9.0, voices=3)


def fmbell(f, dur, vel=0.7, decay=1.2, ratio=1.4142, index=3.0):
    n, t = _ring(dur, decay * 1.5)
    idx = index * np.exp(-t / (decay * 0.4)) + 0.25
    y = np.sin(TWO_PI * f * t + idx * np.sin(TWO_PI * f * ratio * t)) * np.exp(-t / decay)
    y *= np.minimum(1, t / 0.002)
    return _end_fade(y, 80) * vel * 0.45


def digi_arp(f, dur, vel=0.7, bits=6, hold=3):
    y = fmbell(f, dur, vel, decay=0.35, ratio=2.0, index=1.5)
    return bitcrush(lp(y, 8000), bits, hold) * 0.8


def wobble_drone(f, dur, vel=0.6, rate=0.07):
    y = pad(f, dur, vel, bright=0.35, att=min(4.0, dur * 0.4), rel=min(4.0, dur * 0.4), detune=18.0, voices=3)
    t = tarr(y.shape[1])
    ph = rng().uniform(0, TWO_PI)
    return y * (0.65 + 0.35 * np.sin(TWO_PI * rate * t + ph))


# ---- percussion ----------------------------------------------------------

def kick(vel=0.8):
    n = int(0.4 * SR)
    t = tarr(n)
    f = 46 + 95 * np.exp(-t / 0.03)
    ph = TWO_PI * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / 0.13)
    y += 0.18 * bp(noise(n), 1500, 5000) * np.exp(-t / 0.004)
    return fade(y, 0.001, 0.05) * vel * 0.9


def snare(vel=0.8):
    n = int(0.3 * SR)
    t = tarr(n)
    y = 0.5 * np.sin(TWO_PI * 185 * t) * np.exp(-t / 0.05) + 0.7 * bp(noise(n), 1200, 7000) * np.exp(-t / 0.085)
    return fade(y, 0.001, 0.05) * vel * 0.7


def brush(vel=0.7):
    n = int(0.22 * SR)
    t = tarr(n)
    env = np.minimum(1, t / 0.02) * np.exp(-t / 0.07)
    return fade(bp(noise(n), 1500, 6500) * env, 0.003, 0.04) * vel * 0.45


def clap(vel=0.8):
    n = int(0.3 * SR)
    t = tarr(n)
    nz = bp(noise(n), 900, 3800)
    env = sum(np.exp(-np.maximum(t - d, 0) / 0.008) * (t >= d) for d in (0, 0.009, 0.019)) * 0.5
    env += np.exp(-np.maximum(t - 0.019, 0) / 0.09) * (t >= 0.019)
    return fade(nz * env, 0.001, 0.06) * vel * 0.5


def hat(vel=0.6):
    n = int(0.09 * SR)
    t = tarr(n)
    y = lp(hp(noise(n), 6500), 9500) * np.exp(-t / 0.022)
    return fade(y, 0.0008, 0.02) * vel * 0.4


def open_hat(vel=0.6):
    n = int(0.35 * SR)
    t = tarr(n)
    y = lp(hp(noise(n), 6000), 9500) * np.exp(-t / 0.1)
    return fade(y, 0.001, 0.08) * vel * 0.3


def shaker(vel=0.6):
    n = int(0.12 * SR)
    t = tarr(n)
    env = np.minimum(1, t / 0.015) * np.exp(-t / 0.035)
    return fade(bp(noise(n), 3500, 8000) * env, 0.002, 0.03) * vel * 0.4


def tick(vel=0.6, f=2300.0):
    n = int(0.05 * SR)
    t = tarr(n)
    y = np.sin(TWO_PI * f * t) * np.exp(-t / 0.006) + 0.5 * bp(noise(n), 2000, 6000) * np.exp(-t / 0.003)
    return fade(y, 0.0005, 0.012) * vel * 0.5


def tock(vel=0.6):
    return tick(vel, 1500.0)


def rim(vel=0.6):
    n = int(0.08 * SR)
    t = tarr(n)
    y = np.sin(TWO_PI * 1750 * t) * np.exp(-t / 0.012) * 0.6 + bp(noise(n), 1500, 5000) * np.exp(-t / 0.006) * 0.5
    return fade(y, 0.0005, 0.02) * vel * 0.5


def tom(vel=0.7, f0=110.0):
    n = int(0.6 * SR)
    t = tarr(n)
    f = f0 * (1 + 0.5 * np.exp(-t / 0.04))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-t / 0.2)
    y += 0.12 * bp(noise(n), 600, 2500) * np.exp(-t / 0.01)
    return fade(y, 0.001, 0.1) * vel * 0.8


def tom_hi(vel=0.7):
    return tom(vel, 165.0)


def riser(dur, vel=0.6, lo=300, hi=5000):
    n = int(dur * SR)
    t = tarr(n)
    y = bp(noise(n), lo, hi, 2) * (t / dur) ** 2.2
    return fade(y, 0.01, 0.15) * vel * 0.6


def sub_boom(vel=0.8, f0=48.0):
    n = int(2.5 * SR)
    t = tarr(n)
    y = np.sin(TWO_PI * f0 * t * (1 - 0.15 * (1 - np.exp(-t / 0.4)))) * np.exp(-t / 0.9)
    return fade(y, 0.004, 0.2) * vel * 0.8


DRUMS = {
    "k": (kick, 0.0, 0.08), "s": (snare, 0.0, 0.3), "c": (clap, 0.0, 0.35), "b": (brush, 0.1, 0.25),
    "h": (hat, 0.3, 0.1), "o": (open_hat, 0.3, 0.2), "z": (shaker, -0.25, 0.15),
    "t": (tick, 0.2, 0.15), "u": (tock, -0.2, 0.15), "r": (rim, -0.15, 0.2),
    "m": (tom, -0.2, 0.3), "M": (tom_hi, 0.2, 0.3),
}
