"""Song container (wrap-around rendering for seamless loops) and arrangement helpers."""
import re

import numpy as np

import dsp
from dsp import SR, mtof
from instruments import DRUMS

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_QUAL = {
    "": [0, 4, 7], "m": [0, 3, 7], "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "7": [0, 4, 7, 10],
    "sus2": [0, 2, 7], "sus4": [0, 5, 7], "7sus4": [0, 5, 7, 10], "dim": [0, 3, 6], "add9": [0, 4, 7, 14],
    "madd9": [0, 3, 7, 14], "m9": [0, 3, 7, 10, 14], "maj9": [0, 4, 7, 11, 14], "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9], "dim7": [0, 3, 6, 9], "m7b5": [0, 3, 6, 10], "5": [0, 7], "aug": [0, 4, 8],
    "9": [0, 4, 7, 10, 14], "mmaj7": [0, 3, 7, 11],
}


def pc_of(s):
    v = _PC[s[0]]
    for ch in s[1:]:
        v += 1 if ch == "#" else -1
    return v % 12


def midi(name):
    m = re.fullmatch(r"([A-G][#b]?)(-?\d)", name)
    return pc_of(m.group(1)) + 12 * (int(m.group(2)) + 1)


def parse_chord(sym):
    m = re.fullmatch(r"([A-G][#b]?)([^/]*)(?:/([A-G][#b]?))?", sym)
    root = pc_of(m.group(1))
    iv = _QUAL[m.group(2)]
    bass = pc_of(m.group(3)) if m.group(3) else root
    return root, iv, bass


def voice(sym, center=57):
    root, iv, bass = parse_chord(sym)
    pcs = [(root + i) % 12 for i in iv]
    best = None
    for r in range(len(pcs)):
        rot = pcs[r:] + pcs[:r]
        cur = center - 8
        while cur % 12 != rot[0]:
            cur += 1
        notes = [cur]
        for p in rot[1:]:
            nx = notes[-1] + 1
            while nx % 12 != p:
                nx += 1
            notes.append(nx)
        score = abs(np.mean(notes) - center)
        if best is None or score < best[0]:
            best = (score, notes)
    return best[1]


def ladder(sym, low):
    root, iv, _ = parse_chord(sym)
    pcs = {(root + i) % 12 for i in iv}
    return [m for m in range(low, low + 40) if m % 12 in pcs]


def M(text):
    out = []
    for tok in text.split():
        if tok == "|":
            continue
        name, _, d = tok.partition("/")
        out.append((None if name == "r" else midi(name), float(d) if d else 1.0))
    return out


CN_OFFS = [(7, 1.5), (12, 0.5), (14, 1.0), (12, 1.0), (9, 4.0)]


def cn(tonic, minor=False, stretch=1.0):
    """Ciudad Nova leitmotif (sol-do-re-do-la); minor lowers the last degree."""
    return [(tonic + (8 if (o == 9 and minor) else o), d * stretch) for o, d in CN_OFFS]


NOVA_OFFS = [(0, 0.5), (3, 0.5), (6, 0.5), (5, 0.5), (1, 2.0)]


def nova(tonic, stretch=1.0, flip=False):
    """NOVA leitmotif: diminished-flavoured climb that falls to a semitone above the root."""
    notes = [(tonic + o, d * stretch) for o, d in NOVA_OFFS]
    if flip:
        notes = [(2 * tonic + 6 - m, d) for m, d in notes]
    return notes


def parse_prog(text, beats):
    out = []
    for tok in text.split():
        if tok == "|":
            continue
        m = re.fullmatch(r"([^:*]+)(?::([\d.]+))?(?:\*(\d+))?", tok)
        sym = m.group(1)
        if m.group(2):
            out.append((sym, float(m.group(2))))
        else:
            for _ in range(int(m.group(3) or 1)):
                out.append((sym, float(beats)))
    return out


class Arr:
    """Chord timeline built from per-section progression strings."""

    def __init__(self, song, sections):
        self.song = song
        self.tl = []
        self.start_bar = []
        self.n_bars = []
        b = 0.0
        for si, text in enumerate(sections):
            self.start_bar.append(b / song.beats)
            for sym, d in parse_prog(text, song.beats):
                self.tl.append((b, d, sym, si))
                b += d
            self.n_bars.append(b / song.beats - self.start_bar[-1])
        assert abs(b - song.bars * song.beats) < 1e-6, f"{song.name}: progression has {b / song.beats} bars, expected {song.bars}"

    def bar(self, sec, offset=0):
        return int(self.start_bar[sec] + offset)


def _g(gain, b):
    return gain(b) if callable(gain) else gain


def ramp(b0, b1, g0, g1):
    def f(b):
        x = min(1.0, max(0.0, (b - b0) / max(b1 - b0, 1e-9)))
        return g0 + (g1 - g0) * x
    return f


def _stutter(out, i0, sl, reps):
    """Glitch: repeat a short slice, cross-faded in and out so it never clicks."""
    seg = out[:, i0:i0 + sl].copy()
    region = np.tile(seg, (1, reps))
    n = min(region.shape[1], out.shape[1] - i0)
    w = np.ones(n)
    f = int(0.004 * SR)
    w[:f] = np.linspace(0, 1, f)
    w[-f:] = np.linspace(1, 0, f)
    out[:, i0:i0 + n] = out[:, i0:i0 + n] * (1 - w) + region[:, :n] * w


class Song:
    def __init__(self, name, bpm, bars, beats=4, rt60=2.4, wet=1.0, seed=7, idx=0, hum=0.006):
        self.name, self.beats, self.bars = name, beats, bars
        self.spb = 60.0 / bpm
        self.L = int(round(bars * beats * self.spb * SR))
        self.tail = int((rt60 + 6) * SR)
        self.N = self.L + self.tail
        self.dry = np.zeros((2, self.N))
        self.wet = np.zeros((2, self.N))
        self.rt60, self.wetlevel, self.hum, self.seed = rt60, wet, hum, seed * 1000 + idx
        self.rng = np.random.default_rng(self.seed)
        self.stutters = []
        dsp.set_rng(self.seed + 500)

    def vel(self, base, spread=0.07):
        return float(np.clip(base * (1 + self.rng.normal(0, spread)), 0.05, 1.0))

    def put(self, sig, beat, pan=0.0, gain=1.0, send=0.25, hum=None):
        hum = self.hum if hum is None else hum
        t = beat * self.spb + (self.rng.normal() * hum if hum else 0.0)
        i0 = int(round(t * SR))
        if i0 < 0:
            i0 += self.L
        sig = np.asarray(sig, dtype=float)
        if sig.ndim == 1:
            ang = (np.clip(pan, -1, 1) + 1) * np.pi / 4
            sig = np.stack([sig * np.cos(ang), sig * np.sin(ang)]) * np.sqrt(2)
        elif pan:
            ang = (np.clip(pan, -1, 1) + 1) * np.pi / 4
            sig = sig * np.array([[np.cos(ang)], [np.sin(ang)]]) * np.sqrt(2)
        end = min(i0 + sig.shape[1], self.N)
        if end <= i0:
            return
        s = sig[:, : end - i0] * gain
        self.dry[:, i0:end] += s
        self.wet[:, i0:end] += s * send

    def render(self):
        ir = dsp.make_ir(self.rt60, self.seed)
        mix = self.dry + dsp.reverb(self.wet, ir) * self.wetlevel
        nf = int(1.0 * SR)
        mix[:, -nf:] *= np.cos(np.linspace(0, np.pi / 2, nf)) ** 2
        out = mix[:, : self.L].copy()
        rest = mix[:, self.L:]
        pos = 0
        while pos < rest.shape[1]:
            seg = rest[:, pos: pos + self.L]
            out[:, : seg.shape[1]] += seg
            pos += self.L
        for beat, sl, reps in self.stutters:
            _stutter(out, int(beat * self.spb * SR), int(sl * SR), reps)
        return out

    # ---- layers ----
    def pads(self, arr, secs, inst, center=57, gain=0.4, send=0.5, pan=0.0, **kw):
        for b, d, sym, sec in arr.tl:
            if sec in secs:
                for m in voice(sym, center):
                    self.put(inst(mtof(m), d * self.spb, **kw), b, pan, _g(gain, b), send, hum=0.0)

    def bassline(self, arr, secs, pat, inst=None, low=36, gain=0.6, send=0.08, vel=0.8, **kw):
        from instruments import bass as _bass
        inst = inst or _bass
        for b, d, sym, sec in arr.tl:
            if sec not in secs:
                continue
            root, iv, bpc = parse_chord(sym)
            base = low + (bpc - low) % 12
            third = 3 if iv[1] == 3 else 4 if iv[1] == 4 else iv[1]
            for bo in np.arange(0, d, self.beats):
                for ev in pat:
                    off, dur, tone = ev[0], ev[1], ev[2]
                    if bo + off >= d - 1e-9:
                        continue
                    p = {"r": base, "o": base + 12, "f": base + 7, "3": base + third, "l": base + 7 - 12,
                         "s": base + 10, "a": base + 2}[tone]
                    v = self.vel(ev[3] if len(ev) > 3 else vel)
                    self.put(inst(mtof(p), min(dur, d - bo - off) * self.spb, v, **kw), b + bo + off, 0, _g(gain, b), send)

    def arp(self, arr, secs, steps, inst, low=48, gain=0.4, send=0.35, pan=0.0, vel=0.7, **kw):
        for b, d, sym, sec in arr.tl:
            if sec not in secs:
                continue
            lad = ladder(sym, low)
            for bo in np.arange(0, d, self.beats):
                for ev in steps:
                    off, dur, idx = ev[0], ev[1], ev[2]
                    if bo + off >= d - 1e-9:
                        continue
                    v = self.vel(ev[3] if len(ev) > 3 else vel)
                    self.put(inst(mtof(lad[idx]), dur * self.spb, v, **kw), b + bo + off, pan, _g(gain, b), send)

    def mel(self, notes, bar0, inst, gain=0.5, send=0.4, pan=0.0, vel=0.8, transpose=0, beat0=0.0, hum=0.008, **kw):
        b = bar0 * self.beats + beat0
        for m, d in notes:
            if m is not None:
                self.put(inst(mtof(m + transpose), d * self.spb, self.vel(vel, 0.05), **kw), b, pan, _g(gain, b), send, hum=hum)
            b += d

    def chords_hits(self, arr, secs, hits, inst, center=60, gain=0.3, send=0.3, vel=0.7, pan=0.0, **kw):
        """hits: list of (beat_offset, dur_beats) per bar; plays the full voicing."""
        for b, d, sym, sec in arr.tl:
            if sec not in secs:
                continue
            vo = voice(sym, center)
            for bo in np.arange(0, d, self.beats):
                for off, dur in hits:
                    if bo + off >= d - 1e-9:
                        continue
                    for k, m in enumerate(vo):
                        self.put(inst(mtof(m), dur * self.spb, self.vel(vel)), b + bo + off + k * 0.012, pan, _g(gain, b), send, hum=0.0)

    def drums(self, bar0, bar1, pats, gain=1.0, send=None, swing=0.0, vel=0.8, ghost=0.4):
        steps = self.beats * 4
        for bar in range(bar0, bar1):
            for key, pat in pats.items():
                pat = pat.replace("|", "").replace(" ", "")
                fn, pan, snd = DRUMS[key]
                for i in range(steps):
                    c = pat[((bar - bar0) * steps + i) % len(pat)]
                    if c == ".":
                        continue
                    v = min(1.0, vel * 1.25) if c == "X" else vel * ghost if c == "g" else vel
                    beat = bar * self.beats + i * (self.beats / steps)
                    if i % 2 == 1:
                        beat += swing * (self.beats / steps)
                    self.put(fn(self.vel(v, 0.08)), beat, pan, _g(gain, beat), snd if send is None else send, hum=0.004)
