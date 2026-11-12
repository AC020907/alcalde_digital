import re
import unicodedata
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ENDINGS = {
    "informada": "Ciudad Informada",
    "dividida": "Ciudad Dividida",
    "caos": "Caos Informativo",
    "mandato": "Mandato Prestado",
    "secreto": "Fuente Abierta",
}
EndingId = Literal["informada", "dividida", "caos", "mandato", "secreto"]
Mode = Literal["historia", "feria"]
Platform = Literal["pc", "web"]

# Mirrors game/clases/Puntuacion.puntos_investigacion: each satisfied key group ("evidencias")
# is worth 30 and every other clue 6, capped at 60. With at most 3 groups the 150 cap never
# binds, so investigacion == 30 * evidencias + 6 * k for some 0 <= k <= 10.
KEY_GROUP_POINTS = 30
EXTRA_CLUE_POINTS = 6
EXTRA_CLUE_CAP = 60
# The secret ending always adds the non-key clue "conclusion_resonancia" (game/story/novagiro.rpy).
SECRET_MIN_INVESTIGACION = 3 * KEY_GROUP_POINTS + EXTRA_CLUE_POINTS
MAX_DB_INT = 2**31 - 1

ALIAS_RE = re.compile(r"^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ _.\-]+$")

# Matched anywhere in the normalized alias.
_PROFANITY_SUBSTRINGS = (
    "mierda", "pendejo", "cabron", "chingad", "hijueputa", "hijodeputa", "hijoputa",
    "gonorrea", "malparid", "maricon", "nigger", "nigga", "faggot", "fuck", "shit",
    "bitch", "cunt", "whore", "asshole", "bastard",
)
# Short words that appear inside innocent ones (comPUTAdora, VERGAra, AMERICAno);
# matched only as whole tokens.
_PROFANITY_TOKENS = {
    "puta", "puto", "putas", "putos", "culo", "verga", "pija", "marica", "marico",
    "zorra", "slut", "dick", "cock", "ass", "fag",
}
_LEET = str.maketrans("013457@$", "oieastas")


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def contains_profanity(alias: str) -> bool:
    base = _normalize(alias).translate(_LEET)
    squashed = re.sub(r"[^a-z0-9]", "", base)
    if any(word in squashed for word in _PROFANITY_SUBSTRINGS):
        return True
    tokens = {t for t in re.split(r"[^a-z0-9]+", base) if t}
    tokens.add(squashed)  # catches spaced-out spellings such as "p.u.t.a"
    return bool(tokens & _PROFANITY_TOKENS)


def _uuid4(value: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise ValueError("Identificador invalido (se espera uuid4).")
    if parsed.version != 4 or str(parsed) != value.lower():
        raise ValueError("Identificador invalido (se espera uuid4).")
    return str(parsed)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class StartRequest(_Strict):
    player_id: str
    mode: Mode
    platform: Platform
    version: str = Field(min_length=1, max_length=20)

    _pid = field_validator("player_id")(_uuid4)


class Components(_Strict):
    verificacion: int = Field(ge=0, le=300)
    decisiones: int = Field(ge=0, le=250)
    minijuegos: int = Field(ge=0, le=200)
    investigacion: int = Field(ge=0, le=150)
    ciudad: int = Field(ge=0, le=100)

    def total(self) -> int:
        return (self.verificacion + self.decisiones + self.minijuegos
                + self.investigacion + self.ciudad)


class ScoreSubmission(_Strict):
    run_id: str
    player_id: str
    alias: str
    platform: Platform
    mode: Mode
    final: EndingId
    score: int = Field(ge=0, le=1000)
    components: Components
    evidencias: int = Field(ge=0, le=3)
    duration_s: int = Field(ge=0, le=MAX_DB_INT)
    finales_desbloqueados: list[EndingId] = Field(max_length=len(ENDINGS))
    version: str = Field(min_length=1, max_length=20)

    _ids = field_validator("run_id", "player_id")(_uuid4)

    @field_validator("alias")
    @classmethod
    def _alias(cls, value: str) -> str:
        value = value.strip()
        if not 3 <= len(value) <= 20:
            raise ValueError("El alias debe tener entre 3 y 20 caracteres.")
        if not ALIAS_RE.match(value):
            raise ValueError("El alias solo admite letras, numeros, espacios, _, - y .")
        if contains_profanity(value):
            raise ValueError("Alias no permitido. Elige otro.")
        return value

    @model_validator(mode="after")
    def _cross_checks(self):
        c = self.components
        if self.score != c.total():
            raise ValueError("La puntuacion no coincide con la suma de los componentes.")
        if len(set(self.finales_desbloqueados)) != len(self.finales_desbloqueados):
            raise ValueError("finales_desbloqueados contiene duplicados.")
        if self.final not in self.finales_desbloqueados:
            raise ValueError("finales_desbloqueados debe incluir el final obtenido.")
        extra = c.investigacion - KEY_GROUP_POINTS * self.evidencias
        if not (0 <= extra <= EXTRA_CLUE_CAP and extra % EXTRA_CLUE_POINTS == 0):
            raise ValueError("investigacion no es coherente con evidencias.")
        if self.final == "secreto" and not (
                self.evidencias == 3 and c.investigacion >= SECRET_MIN_INVESTIGACION):
            raise ValueError("El final secreto requiere 3 evidencias e investigacion >= 96.")
        if self.final == "caos" and c.ciudad > 50:
            raise ValueError("El final caos requiere ciudad <= 50.")
        if self.final == "informada" and c.ciudad < 50:
            raise ValueError("El final informada requiere ciudad >= 50.")
        return self
