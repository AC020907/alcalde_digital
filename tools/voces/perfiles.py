"""Voice profiles for the Alcalde Digital TTS pipeline. Edit values here and re-run the generator.

pitch: percent offset from the base voice (SSML prosody pitch).
rate: speed multiplier (1.0 = engine default).
gap_ms: extra silence inserted after each sentence (deliberate vs. rushed delivery).
max_pause_ms: longest internal silence kept after synthesis (OneCore adds ~1 s per prosody block).
loudness_offset_db: character offset from the global target loudness.
emotion_scale: multiplies the expression deltas (NOVA stays flat, Martina is very expressive).
tone_db: high-frequency shelf gain (positive = brighter, negative = warmer).
drive: soft saturation amount (0 = off), used for Rodrigo's gruffness.
shift: resample-based pitch+formant shift factor (<1 lowers); the TTS rate is compensated so duration is unchanged.
nova_fx: enables the synthetic NOVA chain (ring mod, bit crush, comb, chorus, stereo widening).
"""

TARGET_LUFS = -16.0
TRUE_PEAK_CEILING_DB = -1.5
OUTPUT_SAMPLE_RATE = 22050
VORBIS_COMPRESSION_LEVEL = 0.6  # libsndfile level 0.6 == Vorbis quality ~0.4
PAD_MS = 60
FADE_MS = 10

PROFILES = {
    "c": {
        "name": "Claudia Reyes",
        "max_pause_ms": 420,
        "voice": "Microsoft Sabina",
        "pitch": -12.0,
        "rate": 0.95,
        "gap_ms": 90,
        "loudness_offset_db": 0.0,
        "emotion_scale": 1.0,
        "tone_db": 0.0,
        "drive": 0.0,
        "shift": 1.0,
    },
    "m": {
        "name": "Martina Sol",
        "max_pause_ms": 300,
        "voice": "Microsoft Sabina",
        "pitch": 20.0,
        "rate": 1.15,
        "gap_ms": 0,
        "loudness_offset_db": 0.5,
        "emotion_scale": 1.3,
        "tone_db": 1.5,
        "drive": 0.0,
        "shift": 1.0,
    },
    "r": {
        "name": "Rodrigo",
        "max_pause_ms": 480,
        "voice": "Microsoft Raul",
        "pitch": -28.0,
        "rate": 0.90,
        "gap_ms": 130,
        "loudness_offset_db": 0.0,
        "emotion_scale": 1.0,
        "tone_db": -3.0,
        "drive": 1.6,
        "shift": 1.0,
    },
    "t": {
        "name": "Tomas Vega",
        "max_pause_ms": 560,
        "voice": "Microsoft Raul",
        "pitch": 0.0,
        "rate": 0.86,
        "gap_ms": 230,
        "loudness_offset_db": 0.0,
        "emotion_scale": 0.7,
        "tone_db": 2.0,
        "drive": 0.0,
        "shift": 1.0,
    },
    "n": {
        "name": "NOVA",
        "max_pause_ms": 380,
        "voice": "Microsoft Sabina",
        "pitch": -25.0,
        "rate": 0.94,
        "gap_ms": 60,
        "loudness_offset_db": -0.5,
        "emotion_scale": 0.2,
        "tone_db": 0.0,
        "drive": 0.0,
        "shift": 0.94,
        "nova_fx": {
            "ring_hz": 45.0,
            "ring_mix": 0.14,
            "crush_hz": 9000,
            "crush_bits": 11,
            "comb_ms": 3.2,
            "comb_gain": 0.33,
            "chorus_mix": 0.30,
            "stereo_delay_ms": 9.0,
        },
    },
}

# Expression attribute (from the Ren'Py script line) -> prosody deltas.
# pitch: percent added; rate: multiplier; loud_db: loudness offset;
# excl_pitch/excl_rate: extra applied to !-segments; emphasis: wrap !-segments in <emphasis>.
EMOTIONS = {
    "feliz": {"pitch": 6.0, "rate": 1.06, "loud_db": 0.5, "excl_pitch": 4.0, "emphasis": False},
    "triste": {"pitch": -6.0, "rate": 0.88, "loud_db": -2.0, "excl_pitch": 0.0, "emphasis": False},
    "enojada": {"pitch": 2.0, "rate": 1.07, "loud_db": 1.5, "excl_pitch": 3.0, "emphasis": True},
    "sorprendida": {"pitch": 9.0, "rate": 1.04, "loud_db": 0.5, "excl_pitch": 3.0, "emphasis": True},
    "seria": {"pitch": -2.0, "rate": 0.95, "loud_db": 0.0, "excl_pitch": 2.0, "emphasis": False},
}
NEUTRAL = {"pitch": 0.0, "rate": 1.0, "loud_db": 0.0, "excl_pitch": 3.0, "emphasis": False}

# Characters never voiced (reason shown in the inventory).
NOT_VOICED = {
    "tu": "jugador (no se dobla)",
    "civitas": "interfaz Civitas (no se dobla)",
    "": "narrador (no se dobla)",
}


# ---------- ElevenLabs (voces humanas y naturales) ----------
# Voice IDs elegidos en la biblioteca de ElevenLabs (espanol latinoamericano). "alt" = segunda opcion para comparar.
# stability: baja = mas expresiva; similarity: fidelidad al timbre; style: exageracion; speed: 0.7-1.2.
ELEVEN_MODEL = "eleven_multilingual_v2"
ELEVEN_VOCES = {
    "c": {"voice_id": "zJtOCbdQjTZt7YZtkRDP", "alt": "jBlmi27XRORxjPquUeCh",   # Natalia; "Brian" resulto voz masculina (~104 Hz)
          "stability": 0.55, "similarity": 0.80, "style": 0.20, "speed": 0.97},
    "m": {"voice_id": "tSnfesUMPgbLTdwP0t2V", "alt": "zJtOCbdQjTZt7YZtkRDP",
          "stability": 0.35, "similarity": 0.80, "style": 0.45, "speed": 1.05},
    "r": {"voice_id": "GTY55jD77hLBRrnQOhNk", "alt": "RyfjEHnKbtma4Srae2za",   # Ludovico (~85 Hz): se distingue de Tomas (~103 Hz)
          "stability": 0.55, "similarity": 0.80, "style": 0.20, "speed": 0.95},
    "t": {"voice_id": "YqZLNYWZm98oKaaLZkUA", "alt": "YqZLNYWZm98oKaaLZkUA",   # el ID alternativo del archivo no existe
          "stability": 0.65, "similarity": 0.80, "style": 0.10, "speed": 0.92},
    "n": {"voice_id": "K3TeN3ZVK8WnOeJ0NYqZ", "alt": "t3eeeqhBjrUqcrPvDqUn",
          "stability": 0.85, "similarity": 0.75, "style": 0.0, "speed": 0.95},
}
# Emocion del guion -> ajuste (menos estabilidad y mas estilo = mas emocion).
ELEVEN_EMOCION = {
    "feliz": {"stability": -0.10, "style": 0.15, "speed": 0.03},
    "triste": {"stability": 0.05, "style": 0.10, "speed": -0.07},
    "enojada": {"stability": -0.15, "style": 0.25, "speed": 0.03},
    "sorprendida": {"stability": -0.12, "style": 0.20, "speed": 0.02},
    "seria": {"stability": 0.08, "style": 0.0, "speed": -0.03},
}


def perfil_eleven(char):
    """Perfil de post-proceso para voces humanas: sin cambios de tono/timbre; solo limpieza, volumen y el efecto de NOVA."""
    base = PROFILES[char]
    return {"name": base["name"], "max_pause_ms": 900, "loudness_offset_db": base.get("loudness_offset_db", 0.0),
            "emotion_scale": base["emotion_scale"], "tone_db": 0.0, "drive": 0.0, "shift": 1.0,
            "nova_fx": base.get("nova_fx")}
