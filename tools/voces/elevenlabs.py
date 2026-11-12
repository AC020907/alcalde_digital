"""ElevenLabs text-to-speech backend for the voice generator (natural, human-sounding voices).

The API key is read from the ELEVENLABS_API_KEY environment variable (also from the Windows user environment,
so `setx` works without restarting the terminal). It is never printed, logged or written to disk.
Audio is requested as raw 16-bit PCM so no decoder is needed; post-processing (trim, loudness, limiter,
NOVA effect) stays in procesado.py.
"""
import json
import os
import time
import urllib.error
import urllib.request

import numpy as np

API = "https://api.elevenlabs.io/v1"
SAMPLE_RATE = 22050


class ErrorElevenLabs(RuntimeError):
    pass


def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key and os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                key = str(winreg.QueryValueEx(k, "ELEVENLABS_API_KEY")[0]).strip()
        except OSError:
            key = ""
    if not key:
        raise ErrorElevenLabs("Falta la variable de entorno ELEVENLABS_API_KEY (usa: setx ELEVENLABS_API_KEY \"...\").")
    return key


class ElevenLabs(object):
    def __init__(self, model_id):
        self.key = api_key()
        self.model_id = model_id
        self.caracteres = 0

    def _peticion(self, metodo, ruta, cuerpo=None, intentos=5):
        datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
        for intento in range(intentos):
            req = urllib.request.Request(API + ruta, data=datos, method=metodo,
                                         headers={"xi-api-key": self.key, "Content-Type": "application/json",
                                                  "Accept": "*/*"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                detalle = e.read()[:400].decode("utf-8", "replace")
                if e.code in (429, 500, 502, 503, 504) and intento < intentos - 1:
                    time.sleep(2 ** intento + 1)
                    continue
                raise ErrorElevenLabs("HTTP %d: %s" % (e.code, detalle))
            except urllib.error.URLError as e:
                if intento < intentos - 1:
                    time.sleep(2 ** intento + 1)
                    continue
                raise ErrorElevenLabs("Sin conexión con ElevenLabs: %s" % e.reason)

    def voz(self, voice_id):
        return json.loads(self._peticion("GET", "/voices/%s" % voice_id))

    def suscripcion(self):
        return json.loads(self._peticion("GET", "/user/subscription"))

    def sintetizar(self, voice_id, texto, ajustes, previo=None, siguiente=None):
        cuerpo = {"text": texto, "model_id": self.model_id, "voice_settings": ajustes}
        if previo:
            cuerpo["previous_text"] = previo
        if siguiente:
            cuerpo["next_text"] = siguiente
        pcm = self._peticion("POST", "/text-to-speech/%s?output_format=pcm_%d" % (voice_id, SAMPLE_RATE), cuerpo)
        self.caracteres += len(texto)
        audio = np.frombuffer(pcm, dtype="<i2").astype(np.float64) / 32768.0
        if not len(audio):
            raise ErrorElevenLabs("ElevenLabs devolvió audio vacío.")
        return audio, SAMPLE_RATE
