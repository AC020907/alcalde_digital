"""Spanish text normalization for TTS (numbers, times, handles, hashtags, acronyms)."""
import re

_ONES = [
    "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
    "once", "doce", "trece", "catorce", "quince", "dieciseis", "diecisiete", "dieciocho",
    "diecinueve", "veinte", "veintiuno", "veintidos", "veintitres", "veinticuatro", "veinticinco",
    "veintiseis", "veintisiete", "veintiocho", "veintinueve",
]
_ONES[16] = "dieciséis"
_ONES[22] = "veintidós"
_ONES[23] = "veintitrés"
_ONES[26] = "veintiséis"
_TENS = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_HUNDREDS = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos",
             "setecientos", "ochocientos", "novecientos"]


def _below_1000(n, apocope):
    if n == 100:
        return "cien"
    h, r = divmod(n, 100)
    parts = []
    if h:
        parts.append(_HUNDREDS[h])
    if r:
        if r < 30:
            word = _ONES[r]
            if apocope and r == 1:
                word = "un"
            elif apocope and r == 21:
                word = "veintiún"
            parts.append(word)
        else:
            t, u = divmod(r, 10)
            word = _TENS[t]
            if u:
                word += " y " + ("un" if (apocope and u == 1) else _ONES[u])
            parts.append(word)
    return " ".join(parts)


def num2es(n, apocope=False):
    if n == 0:
        return "cero"
    if n < 1000:
        return _below_1000(n, apocope)
    if n < 1_000_000:
        th, r = divmod(n, 1000)
        head = "mil" if th == 1 else _below_1000(th, True) + " mil"
        return head + (" " + _below_1000(r, apocope) if r else "")
    m, r = divmod(n, 1_000_000)
    head = "un millón" if m == 1 else num2es(m, True) + " millones"
    return head + (" " + num2es(r, apocope) if r else "")


def _period_of_day(hour24, suffix):
    if suffix == "a":
        return "de la madrugada" if (hour24 == 12 or hour24 < 6) else "de la mañana"
    return "de la tarde" if (hour24 == 12 or hour24 < 7) else "de la noche"


def _time_repl(m):
    h, mi = int(m.group(1)), int(m.group(2))
    suffix = (m.group(3) or "").lower()
    if h > 23 or mi > 59:
        return m.group(0)
    hword = "una" if h == 1 else num2es(h if h != 0 else 12)
    after = m.string[m.end():]
    if mi == 0:
        minutes = "" if re.match(r"\s+en punto", after) else " en punto"
    elif mi == 15:
        minutes = " y cuarto"
    elif mi == 30:
        minutes = " y media"
    else:
        minutes = " y " + num2es(mi)
    out = hword + minutes
    if suffix:
        out += " " + _period_of_day(h, suffix)
        if m.group(0).endswith(".") and (not after.strip() or re.match(r"\s+[A-ZÁÉÍÓÚÑ¿¡]", after)):
            out += "."
    return out


def _camel_split(s):
    s = re.sub(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])", " ", s)
    s = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", s)
    return s


def _handle_repl(m):
    return "arroba " + re.sub(r"[._]+", " ", m.group(1))


def _hashtag_repl(m):
    return "hashtag " + _camel_split(m.group(1).replace("_", " ")).lower()


def _number_repl(m):
    tok = m.group(0)
    if "," in tok:
        whole, frac = tok.split(",", 1)
        whole = whole.replace(".", "")
        return num2es(int(whole)) + " coma " + " ".join(num2es(int(d)) for d in frac)
    return num2es(int(tok.replace(".", "")))


_DICT = [
    (r"\bNOVA\b", "Nova"),
    (r"\bRSN\b", "erre ese ene"),
    (r"\bScheduler\b", "Skéduler"),
    (r"\bOK\b|\bOk\b|\bok\b", "okey"),
    (r"\blive\b|\bLive\b", "láiv"),
    (r"\bEsc\b", "Escape"),
    (r"\bCivitasNet\b", "Cívitas Net"),
    # Se pronuncia CÍ-vi-tas (latin); sin tilde el TTS acentua "ci-VI-tas".
    (r"\bCivitas\b", "Cívitas"),
    (r"\bTV\b", "te ve"),
]


def normalize(raw):
    t = re.sub(r"\{[^}]*\}", "", raw)
    t = t.replace("\\n", " ").replace("\\'", "'")
    t = re.sub(r"[“”«»\"]", "", t)
    t = re.sub(r"(?<!\w)'|'(?!\w)|[‘’]", "", t)
    t = re.sub(r"\blas (?=1:\d\d)", "la ", t)
    t = re.sub(r"\b(\d{1,2}):(\d{2})(?:\s*([aApP])\.?\s?[mM]\.?)?", _time_repl, t)
    t = re.sub(r"@(\w+(?:\.\w+)*)", _handle_repl, t)
    t = re.sub(r"#(\w+)", _hashtag_repl, t)
    t = re.sub(r"%", " por ciento", t)
    for pat, rep in _DICT:
        t = re.sub(pat, rep, t)
    t = re.sub(r"(?<=\w)-(?=\w)", " ", t)
    t = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t)
    t = re.sub(r"\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?", _number_repl, t)
    t = re.sub(r"\s*[—–]\s*", ", ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
