"""A legitimate game client must never be rejected: bodies are built with the game's own code
(game/clases), mirroring game/story/finales.rpy and game/story/leaderboard.rpy."""
import random
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from app import clock
from app.schemas import ALIAS_RE, ScoreSubmission, contains_profanity
from tests.conftest import new_id

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "game" / "clases"))
import Destinos as destinos  # noqa: E402
import Investigacion as inv  # noqa: E402
import Puntuacion as puntuacion  # noqa: E402

ACTIONS = ("verificar_si", "verificar_no", "compartir", "ignorar")
GRADES = ("S", "A", "B", "C", "D", None, "Z")
ALIAS_PREFIXES = ("Ciudadano", "Vecina", "Lector", "Verificadora", "Testigo", "Cronista",
                  "Brigadista")  # ALIAS_PREFIJOS in leaderboard.rpy


def random_minigame(rng):
    kind = rng.random()
    if kind < 0.15:
        return None
    if kind < 0.3:
        return {"exito": False}
    return {"exito": True, "calificacion": rng.choice(GRADES), "perfecto": rng.random() < 0.3}


def random_game_body(rng, mode=None):
    pistas = {p: "observado" for p in inv.PISTAS if rng.random() < rng.random()}
    secret_published = rng.random() < 0.3
    secret_available = inv.final_secreto_disponible({"pistas": pistas})
    if secret_published and secret_available:
        pistas["conclusion_resonancia"] = "comprobado"  # novagiro.rpy, same menu choice
    elif secret_published:
        secret_published = False  # the publish option only exists when the secret is available
    indicadores = {k: rng.randint(0, 100) for k in (
        "info_verificada", "confianza", "convivencia", "bienestar", "desinformacion", "conflictos")}
    final = destinos.decidir_final({
        "forzado": "caos" if rng.random() < 0.05 else None,
        "derrota": rng.random() < 0.05,
        "secreto_publicado": secret_published,
        "secreto_disponible": secret_available,
        "uso_audio": rng.random() < 0.2,
        "viral_ok": rng.random() < 0.6,
        "desinformacion": indicadores["desinformacion"],
        "confianza": indicadores["confianza"],
        "reputacion": rng.randint(0, 100),
        "salud_ciudad": puntuacion.puntos_ciudad(**indicadores),
        "falsas_compartidas": rng.randint(0, 3),
    })
    result = puntuacion.calcular(
        [(rng.randint(0, 100), rng.random() < 0.5, rng.choice(ACTIONS))
         for _ in range(rng.randint(0, 20))],
        {f"d{i}": rng.random() for i in range(rng.randint(0, 12))},
        {m: random_minigame(rng) for m in puntuacion.MINIJUEGOS},
        list(pistas), inv.PISTAS_CLAVE, indicadores, final=final)
    seen = {f for f in destinos.FINALES if rng.random() < 0.3} | {final}
    return {
        "run_id": new_id(), "player_id": new_id(),
        "alias": "%s-%04d" % (rng.choice(ALIAS_PREFIXES), rng.randint(1000, 9999)),
        "platform": rng.choice(("pc", "web")),
        "mode": mode or rng.choice(("feria", "historia")),
        "final": final, "score": result["total"],
        "components": {k: result[k] for k in puntuacion.MAXIMOS},
        "evidencias": sum(inv.grupos_clave({"pistas": pistas}).values()),
        "duration_s": rng.randint(0, 3 * 3600),
        "finales_desbloqueados": [f for f in destinos.FINALES if f in seen],
        "version": "2.0",
    }


def test_server_maxima_match_game():
    assert puntuacion.MAXIMOS == {"verificacion": 300, "decisiones": 250, "minijuegos": 200,
                                  "investigacion": 150, "ciudad": 100}
    assert len(inv.PISTAS_CLAVE) == 3
    assert (puntuacion.PUNTOS_GRUPO_CLAVE, puntuacion.PUNTOS_PISTA_EXTRA,
            puntuacion.TOPE_PISTAS_EXTRA) == (30, 6, 60)
    assert "conclusion_resonancia" in inv.PISTAS
    assert not any("conclusion_resonancia" in ids for ids in inv.PISTAS_CLAVE.values())


def test_random_legit_games_always_validate():
    rng = random.Random(20261104)
    finals = set()
    for _ in range(20000):
        body = random_game_body(rng)
        ScoreSubmission.model_validate(body)  # raises on any false rejection
        finals.add(body["final"])
    assert finals == set(destinos.FINALES)


def test_extreme_legit_games_validate():
    for pistas in ([], list(inv.PISTAS)):
        for final in destinos.FINALES:
            groups = inv.grupos_clave({"pistas": dict.fromkeys(pistas)})
            if final == "secreto" and not all(groups.values()):
                continue
            ind = {k: 100 for k in ("info_verificada", "confianza", "convivencia", "bienestar")}
            ind.update(desinformacion=0, conflictos=0)
            result = puntuacion.calcular([], {}, {}, pistas, inv.PISTAS_CLAVE, ind, final=final)
            ScoreSubmission.model_validate({
                "run_id": new_id(), "player_id": new_id(), "alias": "Ciudadano-1000",
                "platform": "pc", "mode": "feria", "final": final, "score": result["total"],
                "components": {k: result[k] for k in puntuacion.MAXIMOS},
                "evidencias": sum(groups.values()), "duration_s": 0,
                "finales_desbloqueados": [final], "version": "2.0"})


def test_minimal_secret_ending_validates():
    pistas = [ids[0] for ids in inv.PISTAS_CLAVE.values()] + ["conclusion_resonancia"]
    ind = dict.fromkeys(("info_verificada", "confianza", "convivencia", "bienestar",
                         "desinformacion", "conflictos"), 50)
    result = puntuacion.calcular([], {}, {}, pistas, inv.PISTAS_CLAVE, ind, final="secreto")
    assert result["investigacion"] == 96
    ScoreSubmission.model_validate({
        "run_id": new_id(), "player_id": new_id(), "alias": "Testigo-1234", "platform": "web",
        "mode": "historia", "final": "secreto", "score": result["total"],
        "components": {k: result[k] for k in puntuacion.MAXIMOS}, "evidencias": 3,
        "duration_s": 1800, "finales_desbloqueados": ["secreto"], "version": "2.0"})


def test_every_generated_alias_is_accepted():
    for prefix in ALIAS_PREFIXES:
        for n in range(1000, 10000):
            alias = "%s-%04d" % (prefix, n)
            assert ALIAS_RE.match(alias) and not contains_profanity(alias), alias


@pytest.mark.parametrize("mode,minutes", [("feria", 6), ("feria", 10), ("historia", 25),
                                          ("historia", 45)])
def test_real_play_times_are_verified_for_any_score(client, monkeypatch, mode, minutes):
    rng = random.Random(minutes)
    real = clock.utcnow
    elapsed = 0
    for _ in range(40):
        body = random_game_body(rng, mode=mode)
        run = client.post("/api/runs/start", json={
            "player_id": body["player_id"], "mode": mode, "platform": body["platform"],
            "version": "2.0"}).json()
        elapsed += minutes * 60
        monkeypatch.setattr(clock, "utcnow", lambda e=elapsed: real() + timedelta(seconds=e))
        body.update(run_id=run["run_id"], duration_s=minutes * 60 + 2)
        r = client.post("/api/scores", json=body)
        assert r.status_code == 200 and r.json()["verified"] is True, (body, r.text)
        assert {"rank", "top"} <= set(r.json())


def test_offline_client_run_id_is_accepted(client):
    rng = random.Random(7)
    for _ in range(20):
        r = client.post("/api/scores", json=random_game_body(rng))
        assert r.status_code == 200 and r.json()["verified"] is False
