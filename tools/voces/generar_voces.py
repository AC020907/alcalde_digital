"""Generate voice-over OGG files for Ren'Py from a `renpy dialogue` export.

Engines: --motor windows (free offline OneCore TTS) or --motor elevenlabs (natural human voices; needs ELEVENLABS_API_KEY).
  python tools/voces/generar_voces.py --tab dialogue.tab --motor elevenlabs --muestra 3 --out tools/voces/muestras_eleven

Usage:
  python tools/voces/generar_voces.py --tab tools/voces/dialogue_muestra.tab --out tools/voces/muestras
  python tools/voces/generar_voces.py --tab dialogue.tab            # writes game/voice/v2/{Identifier}.ogg
"""
import argparse
import asyncio
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.sax.saxutils import escape

import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import perfiles as P  # noqa: E402
import procesado  # noqa: E402
from texto_es import normalize  # noqa: E402

PIPELINE_VERSION = 2
MOTOR = "windows"
VOZ_ALT = False
# Labels de QA y laboratorio: no son dialogo del juego.
ARCHIVOS_DESARROLLO = ("story/revision_visual.rpy", "minijuegos/laboratorio.rpy", "/qa_")
ELLIPSIS = "§"
PROJECT_ROOT = HERE.parent.parent


def parse_expression(script):
    m = re.match(r'\s*(\w+)((?:\s+\w+)*)\s+"', script or "")
    if not m:
        return ""
    for attr in m.group(2).split():
        if attr in P.EMOTIONS:
            return attr
    return ""


def read_tab(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        if header[:3] != ["Identifier", "Character", "Dialogue"]:
            raise SystemExit(f"Unexpected header in {path}: {header}")
        for r in reader:
            if not r or not r[0].strip():
                continue
            r = r + [""] * (6 - len(r))
            rows.append({"id": r[0].strip(), "char": r[1].strip(), "text": r[2], "file": r[3], "script": r[5]})
    return rows


def classify(row):
    """Fill emotion/normalized text and decide whether the line is voiced (reason when not)."""
    row["emotion"] = parse_expression(row["script"])
    raw = row["text"]
    if any(dev in row.get("file", "").replace("\\", "/") for dev in ARCHIVOS_DESARROLLO):
        row["norm"] = raw
        row["voiced"], row["reason"] = False, "herramienta de desarrollo (no es dialogo del juego)"
        return
    if "[" in raw:
        row["norm"] = raw
        row["voiced"], row["reason"] = False, "interpolacion [..] no se puede pre-grabar"
        return
    row["norm"] = normalize(raw)
    if row["char"] in P.NOT_VOICED:
        row["voiced"], row["reason"] = False, P.NOT_VOICED[row["char"]]
    elif row["char"] not in P.PROFILES:
        row["voiced"], row["reason"] = False, f"personaje '{row['char']}' sin perfil de voz"
    elif not re.search(r"\w", row["norm"]):
        row["voiced"], row["reason"] = False, "texto sin contenido pronunciable"
    else:
        row["voiced"], row["reason"] = True, "ok"


def effective_params(row):
    prof = P.perfil_eleven(row["char"]) if MOTOR == "elevenlabs" else P.PROFILES[row["char"]]
    emo = P.EMOTIONS.get(row["emotion"], P.NEUTRAL)
    return prof, emo


def ajustes_eleven(row):
    v = P.ELEVEN_VOCES[row["char"]]
    e = P.ELEVEN_EMOCION.get(row["emotion"], {})
    escala = P.PROFILES[row["char"]]["emotion_scale"]
    lim = lambda x, a, b: round(max(a, min(b, x)), 3)
    voice_id = v["alt"] if VOZ_ALT else v["voice_id"]
    return voice_id, {"stability": lim(v["stability"] + e.get("stability", 0) * escala, 0, 1),
                      "similarity_boost": v["similarity"],
                      "style": lim(v["style"] + e.get("style", 0) * escala, 0, 1),
                      "speed": lim(v["speed"] + e.get("speed", 0) * escala, 0.7, 1.2),
                      "use_speaker_boost": True}


def line_hash(row):
    prof, emo = effective_params(row)
    payload = {
        "v": PIPELINE_VERSION,
        "text": row["norm"],
        "prof": prof,
        "emo": emo,
        "global": [P.TARGET_LUFS, P.TRUE_PEAK_CEILING_DB, P.OUTPUT_SAMPLE_RATE, P.VORBIS_COMPRESSION_LEVEL,
                   P.PAD_MS, P.FADE_MS],
    }
    if MOTOR == "elevenlabs":   # las voces de Windows conservan su hash: no se regeneran sin motivo
        payload["eleven"] = [P.ELEVEN_MODEL, ajustes_eleven(row)]
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def build_ssml(row):
    prof, emo = effective_params(row)
    scale = prof["emotion_scale"]
    shift = prof.get("shift", 1.0)
    base_pitch = prof["pitch"] + emo["pitch"] * scale
    base_rate = prof["rate"] * (1 + (emo["rate"] - 1) * scale) / shift
    text = row["norm"].replace("...", ELLIPSIS).replace("…", ELLIPSIS)
    pieces = re.findall(r"([^.!?%s]+)([.!?%s]*)" % (ELLIPSIS, ELLIPSIS), text)
    chunks = []
    for i, (body, punct) in enumerate(pieces):
        body = body.strip()
        if not body:
            continue
        last = i == len(pieces) - 1
        has_ell = ELLIPSIS in punct
        clean = punct.replace(ELLIPSIS, "")
        if has_ell and not clean:
            clean = "." if last else ","
        chunks.append((body + clean, "!" in clean or "¡" in body, has_ell))
    parts = []
    for i, (txt, excl, has_ell) in enumerate(chunks):
        pitch, rate = base_pitch, base_rate
        if excl:
            pitch += emo["excl_pitch"] * scale
            rate *= 1.0 + 0.03 * scale
        pitch = max(-35.0, min(35.0, pitch))
        rate = max(0.6, min(1.6, rate))
        inner = escape(txt)
        if excl and emo["emphasis"]:
            inner = f'<emphasis level="moderate">{inner}</emphasis>'
        parts.append(f'<prosody pitch="{pitch:+.1f}%" rate="{rate:.3f}">{inner}</prosody>')
        if i < len(chunks) - 1:
            pause = prof["gap_ms"] if txt[-1] in ".!?" else 0
            if has_ell:
                pause += 380
            if pause:
                parts.append(f'<break time="{int(pause)}ms"/>')
    return ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-MX">'
            + "".join(parts) + "</speak>")


class Synth:
    def __init__(self):
        import winrt.windows.media.speechsynthesis as ss
        import winrt.windows.storage.streams as st
        self.st = st
        self.voices = {v.display_name: v for v in ss.SpeechSynthesizer.all_voices}
        self.synths = {}
        self.ss = ss

    def _get(self, name):
        if name not in self.synths:
            if name not in self.voices:
                raise SystemExit(f"Voz '{name}' no instalada. Disponibles: {sorted(self.voices)}")
            s = self.ss.SpeechSynthesizer()
            s.voice = self.voices[name]
            self.synths[name] = s
        return self.synths[name]

    async def render(self, voice, ssml):
        stream = await self._get(voice).synthesize_ssml_to_stream_async(ssml)
        reader = self.st.DataReader(stream.get_input_stream_at(0))
        await reader.load_async(stream.size)
        buf = bytearray(stream.size)
        reader.read_bytes(buf)
        data, sr = sf.read(io.BytesIO(bytes(buf)), dtype="float64")
        if data.ndim == 2:
            data = data.mean(axis=1)
        return data, sr


def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def manifest_path(out_dir):
    # Ruta relativa al proyecto: el manifiesto sigue valiendo si el repositorio se clona en otra carpeta o equipo.
    try:
        ident = out_dir.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix().lower()
    except ValueError:
        ident = str(out_dir.resolve()).lower()
    key = hashlib.sha1(ident.encode()).hexdigest()[:8]
    return HERE / "manifests" / f"{out_dir.resolve().name}_{key}.json"


def cargar_manifiesto(mpath, out_dir):
    """Lee el manifiesto; si no existe, recupera entradas de manifiestos antiguos (otra ruta absoluta) cuyo audio
    coincide byte a byte con el archivo actual. Asi lo generado por la herramienta no se confunde con grabaciones."""
    if mpath.exists():
        return json.loads(mpath.read_text(encoding="utf-8"))
    entries = {}
    for viejo in sorted(mpath.parent.glob(f"{out_dir.resolve().name}_*.json")):
        for oid, ent in json.loads(viejo.read_text(encoding="utf-8")).get("entries", {}).items():
            f = out_dir / f"{oid}.ogg"
            if oid not in entries and f.exists() and file_sha1(f) == ent.get("out_sha1"):
                entries[oid] = ent
    return {"entries": entries}


def write_inventory(rows, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Identifier", "Character", "emotion", "normalized_text", "voiced", "reason"])
        for r in rows:
            w.writerow([r["id"], r["char"], r["emotion"], r["norm"], "yes" if r["voiced"] else "no", r["reason"]])


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tab", required=True, type=Path, help="Ren'Py dialogue export (.tab)")
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "game" / "voice" / "v2")
    ap.add_argument("--only", default="", help="comma list of character variables, e.g. c,m")
    ap.add_argument("--limit", type=int, default=0, help="synthesize at most N lines")
    ap.add_argument("--force", action="store_true", help="regenerate even if unchanged")
    ap.add_argument("--overwrite-manual", action="store_true",
                    help="also overwrite .ogg files not created by this tool (human recordings)")
    ap.add_argument("--inventario", type=Path, default=HERE / "inventario_voces.csv")
    ap.add_argument("--jobs", type=int, default=4, help="post-processing threads")
    ap.add_argument("--motor", choices=("windows", "elevenlabs"), default="windows")
    ap.add_argument("--alt", action="store_true", help="ElevenLabs: usar la voz alternativa de cada personaje")
    ap.add_argument("--muestra", type=int, default=0,
                    help="solo N lineas por personaje (las mas largas, variando emociones) para comparar voces")
    args = ap.parse_args()
    global MOTOR, VOZ_ALT
    MOTOR, VOZ_ALT = args.motor, args.alt

    rows = read_tab(args.tab)
    seen = set()
    for r in rows:
        if r["id"] in seen:
            print(f"AVISO: Identifier duplicado {r['id']}", file=sys.stderr)
        seen.add(r["id"])
        classify(r)
    write_inventory(rows, args.inventario)

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    mpath = manifest_path(out_dir)
    mpath.parent.mkdir(exist_ok=True)
    manifest = cargar_manifiesto(mpath, out_dir)
    entries = manifest["entries"]

    voiced = {r["id"]: r for r in rows if r["voiced"]}
    only = {c.strip() for c in args.only.split(",") if c.strip()}
    stats = {"generated": 0, "unchanged": 0, "manual_kept": 0, "orphans_removed": 0, "errors": 0}

    for oid in [i for i in entries if i not in voiced]:
        f = out_dir / f"{oid}.ogg"
        if f.exists() and file_sha1(f) == entries[oid].get("out_sha1"):
            f.unlink()
            stats["orphans_removed"] += 1
        del entries[oid]

    todo = []
    for r in rows:
        if not r["voiced"] or (only and r["char"] not in only):
            continue
        h = line_hash(r)
        f = out_dir / f"{r['id']}.ogg"
        ent = entries.get(r["id"])
        if f.exists():
            made_by_tool = ent is not None and file_sha1(f) == ent.get("out_sha1")
            if not made_by_tool and not args.overwrite_manual:
                stats["manual_kept"] += 1
                continue
            if made_by_tool and ent.get("hash") == h and not args.force:
                stats["unchanged"] += 1
                continue
        todo.append((r, h))
    if args.muestra:
        elegidas = []
        for ch in sorted({r["char"] for r, _ in todo}):
            propias = sorted([(r, h) for r, h in todo if r["char"] == ch], key=lambda x: -len(x[0]["norm"]))
            vistas, sel = set(), []
            for r, h in propias:          # primero una por emocion distinta, luego las mas largas
                if r["emotion"] not in vistas:
                    vistas.add(r["emotion"])
                    sel.append((r, h))
            sel += [x for x in propias if x not in sel]
            elegidas += sel[: args.muestra]
        todo = elegidas
    if args.limit:
        todo = todo[: args.limit]
    if MOTOR == "elevenlabs" and todo:
        total = sum(len(r["norm"]) for r, _ in todo)
        print("ElevenLabs: %d lineas, %d caracteres a sintetizar" % (len(todo), total))

    t_synth = 0.0
    t_wall0 = time.perf_counter()
    errors = []

    def post(row, h, raw, sr):
        prof, emo = effective_params(row)
        res = procesado.process(raw, sr, prof, emo["loud_db"] * prof["emotion_scale"],
                                suspensivos=("..." in row["norm"] or "…" in row["norm"]))
        if res is None:
            raise RuntimeError("audio silencioso")
        audio, out_sr, st = res
        f = out_dir / f"{row['id']}.ogg"
        tmp = f.with_suffix(".tmp.ogg")
        decoded, tp = procesado.write_ogg_checked(str(tmp), audio, out_sr, P.TRUE_PEAK_CEILING_DB)
        os.replace(tmp, f)
        st["tp_db"] = round(tp, 2)
        st["lufs"] = round(procesado.measure_lufs(decoded, out_sr), 2)
        st.update({"hash": h, "out_sha1": file_sha1(f), "char": row["char"], "bytes": f.stat().st_size})
        return row["id"], st

    vecinos = {}
    ordenadas = [r for r in rows if r["voiced"]]
    for i, r in enumerate(ordenadas):
        vecinos[r["id"]] = (ordenadas[i - 1]["norm"] if i else None,
                            ordenadas[i + 1]["norm"] if i + 1 < len(ordenadas) else None)

    async def run_eleven():
        nonlocal t_synth
        import elevenlabs as EL
        motor = EL.ElevenLabs(P.ELEVEN_MODEL)
        pool = ThreadPoolExecutor(max_workers=max(1, args.jobs))
        futs = []
        for row, h in todo:
            t0 = time.perf_counter()
            voice_id, ajustes = ajustes_eleven(row)
            previo, siguiente = vecinos.get(row["id"], (None, None))
            try:
                raw, sr = motor.sintetizar(voice_id, row["norm"].replace(ELLIPSIS, "..."), ajustes, previo, siguiente)
            except EL.ErrorElevenLabs as e:
                errors.append((row["id"], "elevenlabs: %s" % e))
                if "HTTP 401" in str(e) or "quota" in str(e).lower() or "Falta" in str(e):
                    break
                continue
            t_synth += time.perf_counter() - t0
            futs.append((row, pool.submit(post, row, h, raw, sr)))
        for row, fut in futs:
            try:
                oid, st = fut.result()
                entries[oid] = st
                stats["generated"] += 1
            except Exception as e:
                errors.append((row["id"], f"post: {e}"))
        pool.shutdown()
        print("Caracteres enviados a ElevenLabs: %d" % motor.caracteres)

    async def run():
        nonlocal t_synth
        if MOTOR == "elevenlabs":
            return await run_eleven()
        synth = Synth()
        pool = ThreadPoolExecutor(max_workers=max(1, args.jobs))
        futs = []
        for row, h in todo:
            t0 = time.perf_counter()
            try:
                raw, sr = await synth.render(effective_params(row)[0]["voice"], build_ssml(row))
            except Exception as e:
                errors.append((row["id"], f"synth: {e}"))
                continue
            t_synth += time.perf_counter() - t0
            futs.append((row, pool.submit(post, row, h, raw, sr)))
        for row, fut in futs:
            try:
                oid, st = fut.result()
                entries[oid] = st
                stats["generated"] += 1
            except Exception as e:
                errors.append((row["id"], f"post: {e}"))
        pool.shutdown()

    if todo:
        asyncio.run(run())
    wall = time.perf_counter() - t_wall0
    stats["errors"] = len(errors)
    mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")

    n_voiced = sum(1 for r in rows if r["voiced"])
    print(f"Inventario: {len(rows)} lineas, {n_voiced} con voz, {len(rows) - n_voiced} omitidas -> {args.inventario}")
    skipped = {}
    for r in rows:
        if not r["voiced"]:
            skipped[r["reason"]] = skipped.get(r["reason"], 0) + 1
    for k, v in sorted(skipped.items()):
        print(f"  omitidas ({v}): {k}")
    print("Resultado:", stats)
    if stats["generated"]:
        print(f"Tiempo: {wall:.1f}s total, {wall / stats['generated']:.2f}s/linea "
              f"(sintesis {t_synth / stats['generated']:.3f}s/linea, resto en post-proceso paralelo)")
    for oid, msg in errors:
        print(f"ERROR {oid}: {msg}", file=sys.stderr)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
