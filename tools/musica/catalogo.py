"""Shared metadata: output locations, expected durations and loudness targets."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MUSIC_DIR = ROOT / "game" / "assets" / "audio" / "music"
SFX_DIR = ROOT / "game" / "assets" / "audio" / "sfx"
SPEC_DIR = Path(__file__).resolve().parent / "espectrogramas"

# name -> (min_seconds, max_seconds, target_lufs)
MUSIC = {
    "menu": (60, 80, -16.0),
    "conversacion": (55, 80, -18.0),
    "investigacion": (55, 80, -18.0),
    "tension": (50, 70, -18.0),
    "crisis": (45, 60, -18.0),
    "nova": (50, 70, -18.0),
    "revelacion": (60, 90, -18.0),
    "calma": (60, 90, -18.0),
    "final_informada": (60, 90, -16.0),
    "final_dividida": (60, 90, -16.0),
    "final_caos": (60, 90, -16.0),
    "final_secreto": (60, 90, -16.0),
    "final_mandato": (60, 90, -16.0),
    "creditos": (60, 90, -16.0),
}

# name -> (min_seconds, max_seconds, peak_dbfs)
SFX = {
    "pista": (0.4, 2.0, -4.5),
    "logro": (0.6, 2.5, -4.5),
    "error": (0.2, 1.0, -4.5),
    "decision": (0.1, 0.8, -4.5),
    "menu_hover": (0.02, 0.3, -14.0),
    "menu_select": (0.1, 0.8, -5.0),
    "pagina": (0.2, 1.0, -4.5),
    "glitch": (0.3, 0.6, -4.5),
    "transicion": (0.6, 2.5, -4.5),
    "voz_blip": (0.02, 0.2, -12.0),
}
