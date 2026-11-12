## Doblaje: cada linea con voz se reproduce sola desde voice/v2/<identificador>.ogg (v2: ruta nueva para que ningun navegador reutilice audios viejos en cache)
## (generadas por tools/voces/generar_voces.py; un actor puede reemplazar cualquier archivo).
## Mientras alguien habla, la musica y los efectos bajan para que la voz se entienda.

define config.auto_voice = "voice/v2/{id}.ogg"
define config.sample_voice = "voice/v2/prologo_cc16fc61.ogg"

define config.emphasize_audio_channels = ["voice"]
define config.emphasize_audio_volume = 0.45
define config.emphasize_audio_time = 0.35

default preferences.emphasize_audio = True
default preferences.voice_sustain = False

## Mezcla inicial: la voz manda, la musica acompaña. El jugador la ajusta en Opciones.
define config.default_music_volume = 0.7
define config.default_sfx_volume = 0.8
define config.default_voice_volume = 1.0
