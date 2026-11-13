"""Compositions. Each builder returns a Song ready to render."""
from functools import partial as P

import numpy as np

import instruments as I
from dsp import bitcrush, lp, mtof
from song import Arr, M, Song, cn, midi, nova, parse_chord, ramp, voice

QUARTER_ARP = [(0, 1, 0), (1, 0.5, 1), (1.5, 0.5, 2), (2, 1, 3), (3, 0.5, 2), (3.5, 0.5, 1)]
EIGHTH_ARP = [(i * 0.5, 0.5, k) for i, k in enumerate([0, 1, 2, 3, 2, 1, 2, 1])]
STRUM_ARP = [(i * 0.5, 0.5, k) for i, k in enumerate([0, 2, 1, 2, 0, 2, 1, 3])]


def curve(song, pts):
    xs = [p[0] * song.beats for p in pts]
    ys = [p[1] for p in pts]
    return lambda b: float(np.interp(b, xs, ys))


def place(s, arr, sec, off_bars, tokens, inst, **kw):
    """Play a melody string starting off_bars into section `sec`."""
    s.mel(M(tokens) if isinstance(tokens, str) else tokens, arr.bar(sec, off_bars), inst, **kw)


# ---------------------------------------------------------------- menu / creditos
MENU_A = "Fmaj7 Am7 Bbmaj7 C Dm7 Am7 Bbmaj7 C7sus4"
MENU_B = "Bbmaj7 C Am7 Dm7 Gm7 C7 Fmaj7 C7sus4"
MENU_A_PH = {
    2: "D5/1 F5/1 A5/1.5 G5/.5 E5/2 r/2",
    4: "F5/1 A5/1 C6/1.5 Bb5/.5 A5/1 G5/1 E5/2",
    6: "D5/1.5 F5/.5 A5/1 G5/1 G5/1 F5/1 C5/2",
}
MENU_A_ALT4 = "A5/1 C6/1 F6/1.5 E6/.5 D6/2 C6/2"
MENU_B_MEL = ("F5/1 A5/1 D6/2 | C6/1 G5/1 E5/2 | E5/1 A5/1 C6/2 | D6/1.5 C6/.5 A5/2 | "
              "G5/1 Bb5/1 D6/2 | E6/1.5 D6/.5 C6/1 Bb5/1 | A5/2 G5/1 F5/1 | G5/2 C5/1 r/1")


def t_menu(seed, idx):
    s = Song("menu", 78, 24, rt60=3.2, seed=seed, idx=idx)
    arr = Arr(s, [MENU_A, MENU_B, MENU_A])
    s.pads(arr, {0, 1, 2}, I.pad, center=57, gain=0.30, send=0.5, bright=0.4)
    s.pads(arr, {1, 2}, I.strings, center=60, gain=0.10, send=0.5)
    s.arp(arr, {0, 2}, QUARTER_ARP, I.epiano, low=48, gain=0.42, send=0.35, vel=0.5)
    s.arp(arr, {1}, EIGHTH_ARP, I.epiano, low=48, gain=0.36, send=0.35, vel=0.5)
    s.bassline(arr, {0, 1, 2}, [(0, 2, "r", 0.7), (2, 1.5, "f", 0.6), (3.5, 0.5, "o", 0.45)], low=36, gain=0.55)
    bell = P(I.bell, decay=2.2)
    for sec in (0, 2):
        s.mel(cn(65), arr.bar(sec), bell, gain=0.5, send=0.45)
        if sec == 2:
            s.mel(cn(65), arr.bar(sec), I.epiano, gain=0.28, send=0.35, vel=0.55)
        for off, tok in MENU_A_PH.items():
            if sec == 2 and off == 4:
                tok = MENU_A_ALT4
            place(s, arr, sec, off, tok, bell, gain=0.5, send=0.45)
    place(s, arr, 1, 0, MENU_B_MEL, I.epiano, gain=0.42, send=0.4, vel=0.65)
    place(s, arr, 1, 0, MENU_B_MEL, bell, gain=0.30, send=0.5, transpose=12)
    s.drums(arr.bar(1), 24, {"z": "x.x.x.x.x.x.x.x.", "k": "x.....g........."}, gain=0.3)
    s.drums(arr.bar(2), 24, {"b": "....x.......x..."}, gain=0.5)
    return s


def t_creditos(seed, idx):
    s = Song("creditos", 88, 28, rt60=2.8, seed=seed, idx=idx)
    bridge = "Dm7 Gm7 Bbmaj7 C Dm7 Bb C C7sus4"
    arr = Arr(s, [MENU_A, MENU_B, bridge, "Fmaj7 Am7 Bbmaj7 C7sus4"])
    allp = {0, 1, 2, 3}
    s.pads(arr, allp, I.pad, center=57, gain=0.28, send=0.5, bright=0.45)
    s.pads(arr, allp, I.strings, center=60, gain=curve(s, [(0, 0.06), (8, 0.14), (16, 0.2), (24, 0.24), (28, 0.2)]), send=0.5)
    s.arp(arr, {0}, QUARTER_ARP, I.piano, low=48, gain=0.5, send=0.3, vel=0.55)
    s.arp(arr, {1, 2, 3}, EIGHTH_ARP, I.piano, low=48, gain=0.45, send=0.3, vel=0.55)
    s.bassline(arr, allp, [(0, 1.5, "r", 0.75), (2, 1, "f", 0.6), (3, 0.5, "r", 0.5), (3.5, 0.5, "o", 0.45)], low=36, gain=0.58)
    bell = P(I.bell, decay=2.2)
    s.mel(cn(65), arr.bar(0), bell, gain=0.5, send=0.45)
    s.mel(cn(65), arr.bar(0), I.strings, gain=0.22, send=0.4)
    for off, tok in MENU_A_PH.items():
        place(s, arr, 0, off, tok, bell, gain=0.5, send=0.45)
    place(s, arr, 1, 0, MENU_B_MEL, I.piano, gain=0.5, send=0.4, vel=0.7)
    place(s, arr, 1, 0, MENU_B_MEL, bell, gain=0.32, send=0.5, transpose=12)
    place(s, arr, 1, 0, MENU_B_MEL, I.strings, gain=0.18, send=0.4)
    place(s, arr, 2, 0, "A5/1 D6/1 F6/2 | G5/1 Bb5/1 D6/2 | F6/2 D6/1 Bb5/1 | E6/2 C6/2 | "
                        "F6/1.5 E6/.5 D6/1 A5/1 | D6/2 F6/2 | G6/2 E6/2 | F6/1 D6/1 C6/2", I.piano, gain=0.45, send=0.4, vel=0.75)
    place(s, arr, 2, 0, "D5/4 | D5/4 | Bb4/4 | C5/4 | D5/4 | D5/4 | E5/4 | C5/4", I.strings, gain=0.2, send=0.4)
    s.mel(cn(65), arr.bar(3), bell, gain=0.5, send=0.45)
    s.mel(cn(65), arr.bar(3), I.strings, gain=0.24, send=0.4)
    s.mel(cn(65), arr.bar(3), I.piano, gain=0.35, send=0.4)
    place(s, arr, 3, 2, "D5/1.5 F5/.5 A5/1 G5/1 G5/1 F5/1 C5/2", bell, gain=0.5, send=0.45)
    s.drums(arr.bar(0) + 4, 28, {"z": "x.x.x.x.x.x.x.x.", "k": "x.......x.......", "r": "....x.......x..."}, gain=0.42)
    s.drums(arr.bar(2), 24, {"h": "x.g.x.g.x.g.x.g.", "c": "....x.......x...", "k": "x.....g.x.g.x..."}, gain=0.4)
    return s


# ---------------------------------------------------------------- conversacion
def t_conversacion(seed, idx):
    s = Song("conversacion", 92, 24, rt60=1.8, seed=seed, idx=idx)
    A = "Cmaj7 Am7 Dm7 G7 Cmaj7 Em7 Fmaj7 G7sus4"
    B = "Am7 Fmaj7 Cmaj7 G Am7 Dm7 Em7 Fmaj7"
    A2 = "Cmaj7 Am7 Dm7 G7 Cmaj7 Fmaj7 Dm7 G7sus4"
    arr = Arr(s, [A, B, A2])
    s.pads(arr, {0, 1, 2}, I.pad, center=57, gain=0.16, send=0.4, bright=0.3)
    gtr = P(I.pluck, tau=0.45, bright=0.5)
    s.arp(arr, {0, 2}, STRUM_ARP, gtr, low=48, gain=0.4, send=0.25, vel=0.5)
    s.chords_hits(arr, {1}, [(0, 0.8), (1.5, 0.4), (2.5, 1.0)], I.epiano, center=62, gain=0.2, send=0.3, vel=0.5)
    s.arp(arr, {1}, [(0.5, 0.5, 2), (3, 0.5, 3)], gtr, low=48, gain=0.3, send=0.3, vel=0.45)
    s.bassline(arr, {0, 1, 2}, [(0, 1.5, "r", 0.7), (2, 1, "f", 0.6), (3, 0.5, "r", 0.5), (3.5, 0.5, "3", 0.45)], low=36, gain=0.55)
    mar = I.marimba
    s.mel(cn(60), arr.bar(0), mar, gain=0.55, send=0.3)
    place(s, arr, 0, 2, "F5/1 E5/1 D5/2 B4/1.5 D5/.5 G4/2", mar, gain=0.55, send=0.3)
    place(s, arr, 0, 4, "r/2 E5/1 D5/1 | E5/1.5 G5/.5 B4/2 | A4/1 C5/1 F5/2 | G5/1.5 F5/.5 D5/2", mar, gain=0.5, send=0.3)
    ep = P(I.epiano)
    place(s, arr, 1, 0, "E5/1.5 E5/.5 A5/1 G5/1 | F5/1.5 A5/.5 C6/2 | B5/1 G5/1 E5/2 | D5/1 G5/1 B5/2 | "
                        "C6/1.5 B5/.5 A5/1 E5/1 | F5/1.5 E5/.5 D5/2 | G5/1 B5/1 E6/2 | C6/2 A5/1 F5/1", ep, gain=0.4, send=0.35, vel=0.6)
    s.mel(cn(60), arr.bar(2), mar, gain=0.5, send=0.3)
    s.mel(cn(60), arr.bar(2), P(I.bell, decay=1.4), gain=0.2, send=0.4, transpose=12)
    place(s, arr, 2, 2, "F5/1 G5/1 A5/1.5 G5/.5 D5/4", mar, gain=0.5, send=0.3)
    place(s, arr, 2, 4, "E5/2 G5/1 C6/1 | A5/2 F5/2 | F5/1 A5/1 D6/2 | C6/1.5 G5/.5 D5/2", mar, gain=0.5, send=0.3)
    s.drums(0, 24, {"z": "X.x.x.x.X.x.x.x.", "h": ".g.g.g.g.g.g.g.g", "b": "....x.......x...", "k": "x.......x......."}, gain=0.5)
    return s


# ---------------------------------------------------------------- investigacion
def t_investigacion(seed, idx):
    s = Song("investigacion", 88, 24, rt60=2.2, seed=seed, idx=idx)
    A = "Dm7*2 G6*2 Fmaj7*2 Am7 Em7"
    B = "Bm7b5*2 Cmaj7*2 Dm7 G6 Am7*2"
    arr = Arr(s, [A, B, A])
    allp = {0, 1, 2}
    ost = [(i * 0.5, 0.4, k, v) for i, (k, v) in enumerate(zip([0, 2, 1, 2, 0, 2, 1, 3], [0.7, 0.4, 0.5, 0.4, 0.6, 0.4, 0.5, 0.45]))]
    s.arp(arr, allp, ost, P(I.pluck, tau=0.12, bright=0.4), low=50, gain=0.45, send=0.25)
    s.bassline(arr, allp, [(0, 4, "r", 0.6)], low=38, gain=0.5, warmth=1.1)
    s.pads(arr, allp, I.pad, center=55, gain=0.2, send=0.5, bright=0.25)
    s.pads(arr, {1}, I.strings, center=58, gain=0.1, send=0.5, tremolo=0.6)
    bell = P(I.bell, decay=1.5)
    place(s, arr, 0, 0, "r/2 D5/1 F5/1 | E5/3 r/1 | r/2 B4/1 D5/1 | C5/3 r/1 | "
                        "A4/1.5 C5/.5 F5/2 | E5/3 r/1 | C5/1 E5/1 A5/2 | G5/2 B4/2", bell, gain=0.45, send=0.5)
    place(s, arr, 1, 0, "F5/1 D5/1 B4/2 | r/4 | G5/2 E5/1 C5/1 | r/4 | A5/1.5 F5/.5 D5/2 | E5/1 G5/1 B5/2 | C6/2 A5/2 | r/4",
          bell, gain=0.45, send=0.5)
    place(s, arr, 2, 0, "r/2 D5/1 F5/1 | E5/3 r/1 | r/2 B4/1 D5/1 | C5/3 r/1 | "
                        "A4/1.5 C5/.5 F5/2 | E5/3 r/1 | C5/1 E5/1 A5/2 | G5/2 B4/2", bell, gain=0.42, send=0.5)
    place(s, arr, 2, 0, "r/2 D6/1 F6/1 | E6/3 r/1 | r/2 B5/1 D6/1 | C6/3 r/1", P(I.bell, decay=0.9, kind="glass"), gain=0.18, send=0.6)
    s.drums(0, 24, {"t": "x.......x.......", "u": "....x.......x..."}, gain=0.35)
    s.drums(arr.bar(1), arr.bar(2), {"m": "x" + "." * 31}, gain=0.35)
    return s


# ---------------------------------------------------------------- tension
def t_tension(seed, idx):
    s = Song("tension", 108, 28, rt60=3.0, seed=seed, idx=idx)
    A = "Am*2 F*2 Am*2 E*2"
    B = "Dm*2 F E Am F Dm E"
    C = "Am F Dm E Am F Dm E"
    D = "Am F Dm E7"
    arr = Arr(s, [A, B, C, D])
    osc = [(0, 0.8, "r", 0.8), (0.5, 0.5, "r", 0.5), (1, 0.5, "o", 0.55), (1.5, 0.5, "r", 0.5),
           (2, 0.5, "r", 0.7), (2.5, 0.5, "r", 0.5), (3, 0.5, "f", 0.55), (3.5, 0.5, "r", 0.5)]
    s.bassline(arr, {0, 1, 2, 3}, osc, low=33, gain=curve(s, [(0, 0.45), (8, 0.5), (16, 0.6), (24, 0.65), (25, 0.45), (28, 0.45)]))
    s.pads(arr, {0, 1, 2, 3}, I.strings, center=57, tremolo=0.45,
           gain=curve(s, [(0, 0.1), (8, 0.2), (16, 0.26), (24, 0.34), (24.01, 0.14), (28, 0.14)]), send=0.5)
    s.pads(arr, {1, 2}, I.pad, center=69, gain=0.06, send=0.6, bright=0.2)
    place(s, arr, 1, 0, "A4/4 | D5/3 C5/1 | C5/4 | B4/2 G#4/2 | E5/3 D5/1 | C5/3 A4/1 | F5/2 E5/2 | E5/4",
          P(I.strings, tremolo=0.5), gain=0.2, send=0.5)
    place(s, arr, 2, 0, "A4/1 C5/1 E5/2 | F5/1 A5/1 C6/2 | D6/2 C6/1 A5/1 | G#5/1 B5/1 E6/2 | "
                        "E5/1 A5/1 C6/2 | A5/1 C6/1 F6/2 | D6/1.5 C6/.5 D6/1 E6/1 | G#5/2 B5/1 E6/1",
          P(I.strings, tremolo=0.5), gain=0.2, send=0.5)
    place(s, arr, 3, 0, "E4/4 | C5/4 | A4/4 | G#4/4", P(I.strings, tremolo=0.3), gain=0.14, send=0.6)
    s.drums(0, 8, {"m": "m" + "." * 31}, gain=0.5)
    s.drums(8, 16, {"m": "m" + "." * 31, "r": "............g...", "t": "x...x...x...x..."}, gain=0.35)
    s.drums(16, 24, {"k": "x...x...x...x...", "s": "........x.......", "h": "x.x.x.x.x.x.x.x."}, gain=0.4)
    s.drums(16, 24, {"u": "....x.......x..."}, gain=0.3)
    s.put(I.riser(4 * s.beats * s.spb, 0.6), 20 * 4, 0, 0.4, 0.5)
    s.put(I.sub_boom(0.9), 24 * 4, 0, 0.7, 0.2)
    return s


# ---------------------------------------------------------------- crisis
def t_crisis(seed, idx):
    s = Song("crisis", 132, 28, rt60=1.6, seed=seed, idx=idx)
    A = "Em*2 F*2 Em*2 Dm F"
    B = "C Dm Em F C Dm Em F"
    C = "Em F Em F Em F Dm F"
    D = "C*2 Dm F"
    arr = Arr(s, [A, B, C, D])
    pat = [(0, 0.5, "r", 0.85), (0.5, 0.5, "r", 0.5), (1, 0.5, "r", 0.7), (1.5, 0.5, "o", 0.6),
           (2, 0.5, "r", 0.8), (2.5, 0.5, "r", 0.5), (3, 0.5, "r", 0.7), (3.5, 0.5, "f", 0.6)]
    s.bassline(arr, {0, 1, 2}, pat, low=40, gain=0.6, send=0.05)
    s.bassline(arr, {3}, [(0, 2, "r", 0.7), (2, 2, "r", 0.6)], low=40, gain=0.5)
    s.pads(arr, {0}, I.strings, center=57, tremolo=0.5, gain=0.12, send=0.5)
    s.pads(arr, {1, 2}, I.strings, center=57, tremolo=0.6, gain=0.2, send=0.5)
    s.chords_hits(arr, {1, 2}, [(0, 0.25), (0.75, 0.25), (1.5, 0.25), (2.5, 0.25)], I.stab, center=64, gain=0.2, send=0.25, vel=0.6)
    ping = P(I.bell, decay=0.35, kind="glass")
    alarm = M("B5/.5 F5/.5 B5/.5 F5/.5 r/2")
    for bar in range(arr.bar(1), arr.bar(2), 2):
        s.mel(alarm, bar, ping, gain=0.22, send=0.35, vel=0.7)
    for bar in range(arr.bar(2), arr.bar(3)):
        s.mel(alarm, bar, ping, gain=0.24, send=0.35, vel=0.75)
    dig = P(I.digi_arp, bits=5, hold=2)
    for bar in (10, 14):
        s.mel(nova(64), bar, dig, gain=0.25, send=0.3)
    for bar in (16, 20):
        s.mel(nova(64), bar, I.stab, gain=0.3, send=0.3, vel=0.8)
    for bar in (18, 22):
        s.mel(nova(64, flip=True), bar, I.stab, gain=0.3, send=0.3, vel=0.8)
    k = "x..g..x.x...x.g."
    s.drums(0, 8, {"k": k, "h": "xgxgxgxgxgxgxgxg"}, gain=0.55)
    s.drums(4, 8, {"s": "....x.......x..."}, gain=0.55)
    s.drums(8, 16, {"k": k, "s": "....x.......x...", "h": "xgxgxgxgxgxgxgxg", "o": "..o...o...o...o."}, gain=0.55)
    s.drums(16, 24, {"k": k, "s": "....x.......x...", "c": "....x.......x...", "h": "xgxgxgxgxgxgxgxg",
                     "o": "..o...o...o...o.", "z": "gggggggggggggggg"}, gain=0.55)
    s.drums(23, 24, {"M": "............xxxx", "m": "..........gg...."}, gain=0.5)
    s.drums(24, 27, {"h": "x.x.x.x.x.x.x.x.", "t": "x...x...x...x..."}, gain=0.4)
    s.drums(27, 28, {"s": "xxxxxxxxxxxxxxxx"}, gain=curve(s, [(27, 0.25), (28, 0.7)]))
    s.put(I.riser(2 * 4 * s.spb, 0.9), 26 * 4, 0, 0.5, 0.4)
    s.put(I.sub_boom(0.8, 41.0), 16 * 4, 0, 0.6, 0.1)
    return s


# ---------------------------------------------------------------- nova
def t_nova(seed, idx):
    s = Song("nova", 116, 28, rt60=3.5, seed=seed, idx=idx)
    A = "C#m*2 A E B C#m A G#7"
    B = "F#m A E B F#m A G#7*2"
    C = "C#m A E B C#m A E G#7"
    D = "C#m*2 A G#7"
    arr = Arr(s, [A, B, C, D])
    allp = {0, 1, 2, 3}
    s.pads(arr, allp, I.pad, center=56, gain=0.3, send=0.55, bright=0.3, detune=26.0)
    s.pads(arr, {1, 2}, I.pad, center=68, gain=0.08, send=0.6, bright=0.2, detune=30.0)
    s.bassline(arr, {0, 1, 2}, [(0, 0.75, "r", 0.8), (1, 0.5, "r", 0.5), (2, 0.75, "r", 0.7), (3, 0.5, "o", 0.5)], low=37, gain=0.55, warmth=2.0)
    mask_a = "x.xx.x.xx.x.xx.x"
    seq = [0, 2, 3, 1, 4, 2, 5, 3, 1, 4, 2, 5, 3, 0, 4, 2]
    dig = P(I.digi_arp, bits=6, hold=3)
    for pan, parity in ((-0.45, 0), (0.45, 1)):
        steps = [(i * 0.25, 0.25, seq[i], 0.55) for i in range(16) if mask_a[i] == "x" and i % 2 == parity]
        s.arp(arr, {1, 2}, steps, dig, low=61, gain=0.35, send=0.35, pan=pan)
        steps = [(i * 0.25, 0.25, seq[i], 0.45) for i in range(16) if mask_a[i] == "x" and i % 2 == parity and i % 4 != 3]
        s.arp(arr, {0}, steps, dig, low=61, gain=0.28, send=0.35, pan=pan)
    glass = P(I.fmbell, decay=1.6, ratio=1.4142, index=3.0)
    for bar in (0, 4):
        s.mel(nova(73, 1.0), bar, glass, gain=0.4, send=0.5)
    for bar in (8, 12, 16, 20):
        s.mel(nova(73, 1.0), bar, glass, gain=0.42, send=0.5)
    for bar in (10, 14, 18, 22):
        s.mel(nova(73, 1.0, flip=True), bar, glass, gain=0.36, send=0.55)
    place(s, arr, 3, 0, "C#5/4 | A4/4 | G#4/4", P(I.fmbell, decay=3.0, ratio=1.4142, index=2.0), gain=0.3, send=0.6)
    s.drums(0, 8, {"k": "x.......x.......", "h": "..x...x...x...x.", "t": "g.g.g.g.g.g.g.g."}, gain=0.45)
    s.drums(8, 24, {"k": "x...x...x...x...", "c": "....x.......x...", "h": "..x...x...x...x.", "t": "xgxgxgxgxgxgxgxg"}, gain=0.42)
    s.drums(16, 24, {"z": "gggggggggggggggg"}, gain=0.45)
    s.drums(24, 28, {"t": "x...x...x...x..."}, gain=0.4)
    s.stutters = [(4 * 7 + 3.0, 0.16, 5), (4 * 15 + 3.0, 0.2, 6), (4 * 19 + 2.5, 0.12, 8), (4 * 23 + 3.25, 0.18, 6), (4 * 26 + 2.0, 0.24, 4)]
    return s


# ---------------------------------------------------------------- revelacion
def t_revelacion(seed, idx):
    s = Song("revelacion", 70, 20, rt60=4.2, seed=seed, idx=idx)
    arr = Arr(s, ["Bbmaj7*2 Gm7*2", "Ebmaj7 Bb/D Cm7 F Gm Eb Bb/D F", "Gm Eb Cm7 F", "Gm Eb Cm7 F7sus4"])
    allp = {0, 1, 2, 3}
    s.pads(arr, allp, I.pad, center=55, bright=0.4, send=0.6,
           gain=curve(s, [(0, 0.04), (4, 0.1), (8, 0.2), (12, 0.3), (13, 0.4), (16, 0.45), (18, 0.2), (20, 0.05)]))
    s.pads(arr, {2, 3}, I.strings, center=60, send=0.55, tremolo=0.25,
           gain=curve(s, [(11.9, 0.0), (12, 0.1), (13, 0.3), (16, 0.38), (17, 0.2), (19, 0.05)]))
    s.bassline(arr, {0}, [(0, 4, "r", 0.4)], inst=I.piano, low=46, gain=0.5, send=0.4)
    s.bassline(arr, {1, 2, 3}, [(0, 3.5, "r", 0.55)], low=34, gain=curve(s, [(4, 0.2), (12, 0.45), (16, 0.5), (19, 0.2)]), send=0.1)
    s.arp(arr, {1}, [(0, 1, 0), (1, 1, 1), (2, 1, 2), (3, 1, 3)], I.piano, low=50, gain=curve(s, [(4, 0.25), (12, 0.45)]), send=0.45, vel=0.5)
    s.arp(arr, {2}, EIGHTH_ARP, I.piano, low=50, gain=0.5, send=0.45, vel=0.62)
    s.arp(arr, {3}, [(0, 1, 0), (2, 1, 2)], I.piano, low=50, gain=curve(s, [(16, 0.4), (20, 0.1)]), send=0.5, vel=0.45)
    bell = P(I.bell, decay=2.4)
    place(s, arr, 0, 2, "D5/4 | F5/4", bell, gain=0.3, send=0.6)
    place(s, arr, 1, 0, "G5/3 F5/1 | D5/2 F5/2 | Eb5/2 G5/2 | F5/4 | D5/1 G5/1 Bb5/2 | Bb5/3 G5/1 | F5/2 D5/2 | A5/1 C6/1 A5/2",
          I.piano, gain=0.55, send=0.5, vel=0.6)
    place(s, arr, 1, 4, "D5/1 G5/1 Bb5/2 | Bb5/3 G5/1 | F5/2 D5/2 | A5/1 C6/1 A5/2", bell, gain=0.25, send=0.6, transpose=12)
    swell = "D6/3 C6/1 | Bb5/2 G5/2 | Eb6/3 D6/1 | C6/2 A5/2"
    place(s, arr, 2, 0, swell, I.piano, gain=0.55, send=0.5, vel=0.8)
    place(s, arr, 2, 0, swell, I.strings, gain=0.3, send=0.5)
    place(s, arr, 2, 0, swell, bell, gain=0.3, send=0.6, transpose=12)
    s.arp(arr, {2}, [(0, 1, 3), (1, 1, 4), (2, 1, 5), (3, 1, 4)], bell, low=72, gain=0.16, send=0.6, vel=0.5)
    place(s, arr, 3, 0, "Bb5/2 G5/2 | G5/3 r/1 | Eb5/4 | r/4", I.piano, gain=0.5, send=0.55, vel=0.55)
    place(s, arr, 3, 0, "Bb5/2 G5/2 | G5/3 r/1", I.strings, gain=0.2, send=0.5)
    s.put(I.riser(3 * 4 * s.spb, 0.8, 400, 5000), 9 * 4, 0, 0.4, 0.6)
    s.put(I.sub_boom(0.9, 49.0), 12 * 4, 0, 0.6, 0.3)
    s.drums(12, 16, {"m": "m" + "." * 15}, gain=0.55)
    return s


# ---------------------------------------------------------------- calma
def t_calma(seed, idx):
    s = Song("calma", 66, 20, rt60=3.4, seed=seed, idx=idx)
    A = "Ebmaj7 Cm7 Abmaj7 Bb Gm7 Cm7 Abmaj7 Bb7sus4"
    B = "Abmaj7 Bb Gm7 Cm7 Fm7 Bb7 Ebmaj7 Bb7sus4"
    C = "Ebmaj7 Cm7 Abmaj7 Bb7sus4"
    arr = Arr(s, [A, B, C])
    allp = {0, 1, 2}
    s.pads(arr, allp, I.pad, center=56, gain=0.22, send=0.55, bright=0.35)
    s.pads(arr, {1}, I.strings, center=60, gain=0.08, send=0.55)
    s.bassline(arr, allp, [(0, 1.5, "r", 0.5), (1.5, 0.5, "f", 0.35), (2, 1, "o", 0.35), (3, 1, "f", 0.3)], inst=I.piano, low=39, gain=0.55, send=0.45)
    place(s, arr, 0, 0, "r/1 Bb4/1 Eb5/2 | G5/3 r/1 | Eb5/1.5 F5/.5 Ab5/2 | G5/2 F5/2 | "
                        "D5/1 G5/1 Bb5/2 | Ab5/1.5 G5/.5 Eb5/2 | C5/1 Eb5/1 Ab5/2 | Bb5/2 Eb5/2", I.piano, gain=0.6, send=0.5, vel=0.55)
    place(s, arr, 1, 0, "C6/3 Bb5/1 | D6/2 Bb5/2 | Bb5/1.5 D6/.5 F6/2 | Eb6/2 C6/2 | "
                        "Ab5/1 C6/1 Eb6/2 | D6/1.5 C6/.5 Ab5/2 | G5/2 Bb5/1 Eb6/1 | Bb5/3 r/1", I.piano, gain=0.6, send=0.5, vel=0.65)
    place(s, arr, 2, 0, "r/1 Bb4/1 Eb5/2 | G5/3 r/1 | Eb5/1.5 F5/.5 Ab5/2 | F5/2 r/2", I.piano, gain=0.6, send=0.5, vel=0.5)
    s.arp(arr, {1}, [(2.5, 1, 5)], P(I.bell, decay=2.5), low=72, gain=0.14, send=0.65, vel=0.5)
    return s


# ---------------------------------------------------------------- finales
def t_final_informada(seed, idx):
    s = Song("final_informada", 84, 24, rt60=2.2, seed=seed, idx=idx)
    A = "D A/C# Bm7 G D A G A7sus4"
    B = "Gmaj7 A F#m7 Bm7 Gmaj7 A D A7sus4"
    A2 = "D A/C# Bm7 G Gmaj7 A Bm7 A7sus4"
    arr = Arr(s, [A, B, A2])
    allp = {0, 1, 2}
    s.pads(arr, allp, I.pad, center=57, gain=0.24, send=0.5, bright=0.5)
    s.pads(arr, {1, 2}, I.strings, center=62, gain=0.14, send=0.5)
    s.arp(arr, allp, STRUM_ARP, P(I.pluck, tau=0.5, bright=0.55), low=50, gain=0.38, send=0.3, vel=0.55)
    s.bassline(arr, allp, [(0, 1.5, "r", 0.75), (2, 1, "f", 0.6), (3, 0.5, "r", 0.5), (3.5, 0.5, "o", 0.45)], low=38, gain=0.58)
    bell = P(I.bell, decay=2.0)
    s.mel(cn(62), arr.bar(0), bell, gain=0.5, send=0.4)
    s.mel(cn(62), arr.bar(0), I.epiano, gain=0.3, send=0.35, vel=0.6)
    tail = "F#5/1 A5/1 B5/1.5 A5/.5 G5/2 B5/1 D6/1 | A5/1.5 F#5/.5 A5/1 D6/1 C#6/1 E6/1 A5/2 | B5/1 D6/1 G6/2 E6/1.5 D6/.5 A5/2"
    place(s, arr, 0, 2, tail, bell, gain=0.5, send=0.4)
    place(s, arr, 0, 2, tail, I.epiano, gain=0.28, send=0.35, vel=0.6)
    B_MEL = ("B5/1.5 D6/.5 F#6/2 | E6/2 C#6/2 | A5/1 C#6/1 F#6/2 | D6/1.5 B5/.5 F#5/2 | "
             "G5/1 B5/1 D6/2 | E6/1.5 D6/.5 C#6/2 | D6/2 A5/1 F#5/1 | A5/2 r/2")
    place(s, arr, 1, 0, B_MEL, bell, gain=0.5, send=0.45)
    place(s, arr, 1, 0, B_MEL, I.epiano, gain=0.32, send=0.35, vel=0.65)
    place(s, arr, 1, 0, B_MEL, I.strings, gain=0.14, send=0.4)
    s.mel(cn(62), arr.bar(2), bell, gain=0.5, send=0.4)
    s.mel(cn(62), arr.bar(2), I.strings, gain=0.2, send=0.4)
    tail2 = "D6/1 B5/1 F#5/2 G5/1.5 B5/.5 D6/2 | B5/2 D6/2 C#6/2 E6/2 | D6/1.5 B5/.5 F#5/2 A5/3 r/1"
    place(s, arr, 2, 2, tail2, bell, gain=0.5, send=0.4)
    place(s, arr, 2, 2, tail2, I.epiano, gain=0.28, send=0.35, vel=0.65)
    s.drums(0, 24, {"z": "x.x.x.x.x.x.x.x.", "k": "x.......x..g.x..", "r": "....x.......x..."}, gain=0.45)
    s.drums(8, 24, {"c": "....x.......x..."}, gain=0.3)
    return s


def t_final_dividida(seed, idx):
    s = Song("final_dividida", 72, 20, rt60=3.2, seed=seed, idx=idx)
    A = "Am Fmaj7 C G/B Am Fmaj7 Dm7 E7"
    B = "C G Am F C G F C"
    C = "Am F C E7sus4"
    arr = Arr(s, [A, B, C])
    allp = {0, 1, 2}
    s.pads(arr, allp, I.pad, center=55, gain=0.24, send=0.55, bright=0.3)
    s.pads(arr, {1}, I.strings, center=60, gain=0.12, send=0.55)
    s.arp(arr, allp, [(0, 1, 0), (1, 0.5, 1), (1.5, 0.5, 2), (2, 1, 3), (3, 1, 2)], I.piano, low=45, gain=0.4, send=0.4, vel=0.5)
    s.bassline(arr, allp, [(0, 3.5, "r", 0.55)], low=33, gain=0.5)
    place(s, arr, 0, 0, "E5/1.5 C5/.5 D5/1 B4/1 | C5/2 A4/2 | G4/1 C5/1 E5/2 | D5/2 B4/2 | "
                        "E5/1.5 A5/.5 G5/1 E5/1 | F5/2 C5/1 A4/1 | D5/1.5 F5/.5 A5/2 | G#5/2 B5/1 r/1", I.piano, gain=0.6, send=0.5, vel=0.6)
    cello = P(I.strings)
    mb = "E5/2 G5/2 | B4/1 D5/1 G5/2 | A5/1.5 G5/.5 E5/2 | F5/2 A5/1 C6/1 | E6/2 C6/2 | D6/1.5 B5/.5 G5/2 | A5/1 C6/1 F6/2 | C6/2 G5/2"
    place(s, arr, 1, 0, mb, I.piano, gain=0.55, send=0.5, vel=0.65)
    place(s, arr, 1, 0, "C4/4 | G3/4 | A3/4 | F3/4 | C4/4 | G3/4 | F3/4 | E4/4", cello, gain=0.22, send=0.5)
    place(s, arr, 1, 0, "E4/4 | D4/4 | C4/4 | A3/4 | E4/4 | D4/4 | C4/4 | G4/4", cello, gain=0.14, send=0.5)
    place(s, arr, 2, 0, "E5/1.5 C5/.5 D5/1 B4/1 | C5/2 A4/2 | G4/1 C5/1 E5/2 | A4/2 B4/1 r/1", I.piano, gain=0.6, send=0.5, vel=0.55)
    s.drums(arr.bar(1), arr.bar(2), {"b": "....x.......x...", "z": "g.g.g.g.g.g.g.g."}, gain=0.35)
    return s


def t_final_caos(seed, idx):
    s = Song("final_caos", 60, 16, rt60=5.5, wet=1.15, seed=seed, idx=idx, hum=0.0)
    L = s.bars * s.beats
    sets = [[33, 34, 40, 41, 54], [32, 33, 39, 40, 52]]
    for si, notes in enumerate(sets):
        for j, m in enumerate(notes):
            s.put(I.wobble_drone(mtof(m), 8 * 4 * s.spb, 0.7 - 0.05 * j, rate=0.05 + 0.02 * j), si * 32, (j - 2) * 0.3, 0.35, 0.6, hum=0.0)
    s.put(I.pad(mtof(81), 28 * s.spb, 0.4, bright=0.15, att=8, rel=8, detune=40, voices=3), 6, 0, 0.12, 0.8, hum=0.0)
    s.put(I.pad(mtof(82), 28 * s.spb, 0.4, bright=0.15, att=8, rel=8, detune=40, voices=3), 36, 0, 0.12, 0.8, hum=0.0)

    def notif(f, dur, vel):
        y = I.fmbell(f, 0.05, vel, decay=0.45, ratio=1.5, index=2.5)
        y = np.tanh(3.0 * y) / np.tanh(3.0)
        return bitcrush(lp(y, 5000), 5, 3) * 0.7

    r = s.rng
    motif = [m for m, _ in nova(81)]
    for ev in range(16):
        beat = ev * (L / 16) + r.uniform(0.2, 3.0)
        k = int(r.integers(0, 4))
        notes = [motif[k], motif[(k + 1) % 5]] if r.random() < 0.6 else [motif[k]]
        pan0 = r.uniform(-0.8, 0.8)
        for j, m in enumerate(notes):
            for tap in range(4):
                s.put(notif(mtof(m), 0.1, 0.6), beat + j * 0.33 + tap * 1.1, pan0 * (-1) ** tap, 0.16 * 0.5 ** tap, 0.9, hum=0.0)
    for bar in (3, 7, 11, 14):
        s.put(I.riser(3.5 * s.spb * 4, 0.8, 120, 3000), bar * 4, 0, 0.35, 0.8, hum=0.0)
    for bar in range(8, 16):
        s.put(I.sub_boom(0.8, 44.0), bar * 4, 0, 0.5, 0.4, hum=0.0)
        s.put(I.sub_boom(0.5, 44.0), bar * 4 + 0.45, 0, 0.35, 0.4, hum=0.0)
    s.stutters = [(4 * 5 + 1.5, 0.07, 6), (4 * 9 + 2.75, 0.1, 5), (4 * 12 + 0.5, 0.06, 8), (4 * 14 + 3.2, 0.09, 6)]
    return s


def t_final_secreto(seed, idx):
    s = Song("final_secreto", 96, 28, rt60=2.4, seed=seed, idx=idx)
    A = "G D/F# Em7 C G/B Am7 C D"
    B = "C D Bm7 Em C D G D"
    C = "G D Em C G D C D"
    D = "Em C Am7 D7sus4"
    arr = Arr(s, [A, B, C, D])
    allp = {0, 1, 2, 3}
    s.pads(arr, allp, I.pad, center=57, gain=0.22, send=0.5, bright=0.5)
    s.pads(arr, {1, 2, 3}, I.strings, center=62, gain=curve(s, [(8, 0.1), (16, 0.2), (24, 0.26), (28, 0.2)]), send=0.5)
    s.arp(arr, {0, 1}, STRUM_ARP, P(I.pluck, tau=0.5, bright=0.55), low=50, gain=0.38, send=0.3, vel=0.55)
    s.arp(arr, {2, 3}, EIGHTH_ARP, I.piano, low=50, gain=0.38, send=0.3, vel=0.6)
    s.bassline(arr, allp, [(0, 1.5, "r", 0.75), (2, 1, "f", 0.6), (3, 0.5, "r", 0.5), (3.5, 0.5, "o", 0.45)], low=36, gain=0.6)
    bell = P(I.bell, decay=2.0)
    s.mel(cn(67), arr.bar(0), bell, gain=0.5, send=0.4)
    s.mel(cn(67), arr.bar(0), I.epiano, gain=0.3, send=0.35, vel=0.6)
    place(s, arr, 0, 2, "B4/1 D5/1 G5/2 | A4/1 C5/1 E5/2 | E5/1 G5/1 B5/2 | G5/1.5 E5/.5 C5/2", bell, gain=0.45, send=0.4)
    place(s, arr, 0, 6, "G5/1 B5/1 D6/2 | F#5/1 A5/1 D6/2", bell, gain=0.45, send=0.4)
    rise = ("C5/1 E5/1 G5/2 | D5/1 F#5/1 A5/2 | F#5/1 A5/1 D6/2 | G5/1 B5/1 E6/2 | "
            "E5/1 G5/1 C6/2 | F#5/1 A5/1 D6/2 | B5/1 D6/1 G6/2 | F#6/1.5 D6/.5 A5/2")
    place(s, arr, 1, 0, rise, bell, gain=0.45, send=0.4)
    place(s, arr, 1, 0, rise, I.epiano, gain=0.3, send=0.35, vel=0.65)
    place(s, arr, 1, 0, rise, I.strings, gain=0.14, send=0.4)
    triumph = ("D5/1.5 G5/.5 A5/1 G5/1 E5/4 | B5/1 D6/1 E6/1.5 D6/.5 | C6/2 G5/2 | "
               "D5/1.5 G5/.5 A5/1 B5/1 | D6/4 | E6/1.5 D6/.5 C6/1 A5/1 | B5/2 A5/1 F#5/1")
    place(s, arr, 2, 0, triumph, bell, gain=0.5, send=0.4)
    place(s, arr, 2, 0, triumph, I.strings, gain=0.28, send=0.4)
    place(s, arr, 2, 0, triumph, I.epiano, gain=0.3, send=0.35, vel=0.7)
    place(s, arr, 3, 0, "G5/2 E5/2 | G5/2 C6/2 | A5/2 E5/2 | D5/3 r/1", bell, gain=0.45, send=0.45)
    place(s, arr, 3, 0, "G5/2 E5/2 | G5/2 C6/2 | A5/2 E5/2 | D5/3 r/1", I.strings, gain=0.2, send=0.45)
    s.chords_hits(arr, {2}, [(0, 0.5), (1.5, 0.5)], I.stab, center=62, gain=0.12, send=0.3, vel=0.6)
    s.drums(0, 8, {"z": "x.x.x.x.x.x.x.x.", "k": "x.......x.......", "r": "....x.......x..."}, gain=0.42)
    s.drums(8, 16, {"k": "x...x...x...x...", "c": "....x.......x...", "z": "x.x.x.x.x.x.x.x."}, gain=0.42)
    s.drums(16, 24, {"k": "x..gx..gx..gx.g.", "s": "....x.......x...", "c": "....x.......x...", "o": "..o...o...o...o.", "h": "x.x.x.x.x.x.x.x."}, gain=0.5)
    s.drums(24, 28, {"k": "x.......x......."}, gain=0.4)
    s.put(I.riser(2 * 4 * s.spb, 0.8), 14 * 4, 0, 0.5, 0.4)
    s.put(I.sub_boom(0.9, 49.0), 16 * 4, 0, 0.6, 0.2)
    return s


def t_final_mandato(seed, idx):
    s = Song("final_mandato", 100, 40, beats=3, rt60=2.6, seed=seed, idx=idx, hum=0.012)
    cell = "Bm G Em F#7"
    arr = Arr(s, [cell, "Bm G Em F#7 Bm G Em7 F#", "G D Em F#7 G D Em F#",
                  "Bm G Em F#7 Bm G Em7 F# Bm Em Bm F#7", "Bm G Em F#7 Bm G Em F#7"])
    r = s.rng
    allp = {0, 1, 2, 3, 4}
    s.bassline(arr, allp, [(0, 0.9, "r", 0.7)], inst=P(I.pluck, tau=0.3, bright=0.25), low=35, gain=0.6, send=0.2)
    s.chords_hits(arr, {1, 2, 3, 4}, [(1, 0.5), (2, 0.5)], P(I.pluck, tau=0.18, bright=0.25), center=60, gain=0.2, send=0.25, vel=0.5)
    for b, d, sym, sec in arr.tl:
        root, iv, bpc = parse_chord(sym)
        base = 47 + (root - 47) % 12
        g = 0.14 if sec else 0.1
        for m in (base, base + 7, base + 12):
            s.put(I.pad(mtof(m), d * s.spb, 0.5, bright=0.15, att=0.9, rel=1.0, detune=14.0, voices=3), b, 0, g, 0.5, hum=0.0)

    def box_for(sd):
        def box(f, dur, vel):
            return I.musicbox(f, dur, vel, detune_cents=-14 + r.normal(0, sd))
        return box

    mb = box_for(14)
    mb_bad = box_for(40)
    m2 = ("F#5/1 B5/1 D6/1 | D6/1.5 B5/.5 G5/1 | G5/1 B5/1 E6/1 | C#6/2 A#5/1 | "
          "F#5/1 B5/1 D6/1 | B5/1 G5/1 B5/1 | E6/2 D6/1 | C#6/2 r/1")
    place(s, arr, 0, 2, "F#5/3 | r/3", mb, gain=0.5, send=0.5, vel=0.5)
    place(s, arr, 1, 0, m2, mb, gain=0.55, send=0.45)
    place(s, arr, 2, 0, "G5/1 B5/1 D6/1 | A5/1 D6/1 F#6/1 | G6/2 E6/1 | C#6/1 A#5/1 F#5/1 | "
                        "B5/1 D6/1 G6/1 | F#6/2 D6/1 | E6/1 B5/1 G5/1 | A#5/2 r/1", mb, gain=0.55, send=0.45)
    place(s, arr, 2, 0, "G5/1 B5/1 D6/1 | A5/1 D6/1 F#6/1 | G6/2 E6/1 | C#6/1 A#5/1 F#5/1 | "
                        "B5/1 D6/1 G6/1 | F#6/2 D6/1 | E6/1 B5/1 G5/1 | A#5/2 r/1", mb_bad, gain=0.2, send=0.5, transpose=-12)
    place(s, arr, 3, 0, m2, mb, gain=0.55, send=0.45)
    place(s, arr, 3, 0, m2, mb_bad, gain=0.22, send=0.5, transpose=-12)
    place(s, arr, 3, 8, "B5/2 D6/1 | G5/1 B5/1 E6/1 | D6/2 B5/1 | A#5/3", mb, gain=0.55, send=0.45)
    place(s, arr, 4, 0, "F#5/1 B5/1 D6/1 | D6/1.5 B5/.5 G5/1 | G5/1 B5/1 E6/1 | C#6/2 A#5/1", mb_bad, gain=0.5, send=0.55)
    place(s, arr, 4, 4, "F#5/1 r/2 | r/3 | B5/3 | r/3", mb_bad, gain=0.45, send=0.6)
    s.drums(arr.bar(3), arr.bar(4), {"b": "....x...x..."}, gain=0.25)
    s.put(I.bell(mtof(midi("F#6")), 0.2, 0.4, decay=1.6, kind="glass"), arr.bar(3) * 3, 0, 0.2, 0.6)
    return s


BUILDERS = {
    "menu": t_menu, "conversacion": t_conversacion, "investigacion": t_investigacion, "tension": t_tension,
    "crisis": t_crisis, "nova": t_nova, "revelacion": t_revelacion, "calma": t_calma,
    "final_informada": t_final_informada, "final_dividida": t_final_dividida, "final_caos": t_final_caos,
    "final_secreto": t_final_secreto, "final_mandato": t_final_mandato, "creditos": t_creditos,
}
