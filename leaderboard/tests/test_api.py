from datetime import timedelta

import pytest

from app import clock
from tests.conftest import new_id, payload, with_components

ADMIN = "a" * 32


def post(client, **kw):
    return client.post("/api/scores", json=payload(**kw))


def start(client, player_id, mode="historia", platform="pc"):
    r = client.post("/api/runs/start", json={"player_id": player_id, "mode": mode,
                                              "platform": platform, "version": "2.0"})
    assert r.status_code == 200
    return r.json()


def advance(monkeypatch, seconds):
    real = clock.utcnow
    monkeypatch.setattr(clock, "utcnow", lambda: real() + timedelta(seconds=seconds))


@pytest.fixture
def post_verified(client, monkeypatch):
    """Start a run, let `play_s` seconds pass on the server clock, then submit it."""
    def submit(c=None, play_s=1700, **kw):
        c = c or client
        body = payload(**kw)
        run = start(c, body["player_id"], body["mode"], body["platform"])
        advance(monkeypatch, play_s)
        body["run_id"] = run["run_id"]
        r = c.post("/api/scores", json=body)
        assert r.status_code == 200 and r.json()["verified"] is True, r.text
        return r
    return submit


def board(client, qs="mode=historia"):
    return client.get("/api/leaderboard?" + qs).json()["entries"]


# ---- basics -------------------------------------------------------------

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"ok": True}


def test_index_page_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "Tabla de Honor" in r.text and "/static/qr.png" in r.text


def test_qr_served_only_when_generated(client):
    # tools/web/generar_qr.py crea el QR solo cuando la URL del juego ya funciona.
    from pathlib import Path
    existe = (Path(__file__).resolve().parent.parent / "app" / "static" / "qr.png").exists()
    r = client.get("/static/qr.png")
    if existe:
        assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    else:
        assert r.status_code == 404


def test_not_found_error_shape(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and set(r.json()) == {"error", "detail"}


def test_docs_disabled(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


# ---- happy path ---------------------------------------------------------

def test_submit_verified_happy_path(post_verified):
    data = post_verified().json()
    assert data["accepted"] is True and data["verified"] is True and data["ranked"] is True
    assert data["rank"] == 1 and data["personal_best"] == 742 and data["duplicate"] is False
    top = data["top"][0]
    assert top["alias"] == "Ciudadano-4821" and top["final_title"] == "Ciudad Informada"
    assert set(top) == {"rank", "alias", "score", "final", "final_title", "mode",
                        "platform", "verified", "created_at"}


def test_unverified_is_stored_but_not_public(client, post_verified):
    post_verified(alias="Verificado", **with_components(verificacion=100))  # 602
    r = post(client, alias="SinVerificar")  # 742, client-generated run_id
    data = r.json()
    assert r.status_code == 200 and data["verified"] is False and data["ranked"] is False
    assert data["personal_best"] == 742
    assert data["rank"] == 1  # where it would be among public entries
    assert [e["alias"] for e in data["top"]] == ["Verificado"]
    assert [e["alias"] for e in board(client)] == ["Verificado"]
    full = board(client, "mode=historia&include_unverified=1")
    assert [e["alias"] for e in full] == ["SinVerificar", "Verificado"]


def test_unverified_rank_ignores_own_public_entry(client, post_verified):
    pid = new_id()
    post_verified(player_id=pid, **with_components(verificacion=100))  # 602
    post_verified(**with_components(verificacion=200))  # 702, other player
    data = post(client, player_id=pid).json()  # 742 unverified
    assert data["verified"] is False and data["ranked"] is True
    assert data["personal_best"] == 742 and data["rank"] == 2  # public entry is 602


def test_alias_is_trimmed(post_verified):
    assert post_verified(alias="  Ana María  ").json()["top"][0]["alias"] == "Ana María"


# ---- validation ---------------------------------------------------------

def test_sum_mismatch(client):
    assert post(client, score=741).status_code == 422


def test_score_over_1000(client):
    assert post(client, score=1001).status_code == 422


@pytest.mark.parametrize("comp,val", [("verificacion", 301), ("decisiones", 251),
                                      ("minijuegos", 201), ("investigacion", 156),
                                      ("ciudad", 101), ("ciudad", -1)])
def test_component_over_max(client, comp, val):
    assert post(client, **with_components(**{comp: val})).status_code == 422


def test_unknown_final_mode_platform(client):
    assert post(client, final="otro").status_code == 422
    assert post(client, mode="x").status_code == 422
    assert post(client, platform="ios").status_code == 422


def test_evidencias_range(client):
    assert post(client, evidencias=4).status_code == 422
    assert post(client, evidencias=-1).status_code == 422


def test_strict_types(client):
    assert post(client, score="742").status_code == 422
    assert post(client, evidencias=True).status_code == 422


def test_finales_rules(client):
    assert post(client, finales_desbloqueados=["dividida"]).status_code == 422
    assert post(client, finales_desbloqueados=["informada", "informada"]).status_code == 422
    assert post(client, finales_desbloqueados=["informada", "zzz"]).status_code == 422


@pytest.mark.parametrize("evidencias,investigacion,status", [
    (0, 0, 200), (0, 60, 200), (0, 66, 422), (0, 5, 422),
    (1, 30, 200), (1, 24, 422), (1, 90, 200), (1, 96, 422),
    (2, 60, 200), (2, 92, 422), (2, 120, 200),
    (3, 90, 200), (3, 150, 200), (3, 84, 422), (3, 100, 422)])
def test_investigacion_matches_evidencias(client, evidencias, investigacion, status):
    r = post(client, final="dividida", finales_desbloqueados=["dividida"],
             evidencias=evidencias, **with_components(investigacion=investigacion))
    assert r.status_code == status


def test_secreto_cross_check(client):
    def secreto(evidencias, investigacion):
        return post(client, final="secreto", evidencias=evidencias,
                    finales_desbloqueados=["secreto"],
                    **with_components(investigacion=investigacion)).status_code

    assert secreto(3, 96) == 200
    assert secreto(3, 150) == 200
    assert secreto(3, 90) == 422
    assert secreto(2, 102) == 422


def test_caos_cross_check(client):
    assert post(client, final="caos", finales_desbloqueados=["caos"],
                **with_components(ciudad=51)).status_code == 422
    assert post(client, final="caos", finales_desbloqueados=["caos"],
                **with_components(ciudad=50)).status_code == 200


def test_informada_cross_check(client):
    assert post(client, **with_components(ciudad=49)).status_code == 422
    assert post(client, **with_components(ciudad=50)).status_code == 200


@pytest.mark.parametrize("alias", ["ab", "x" * 21, "   ", "hola<script>", "emoji\U0001F600ok", "a/b/c"])
def test_bad_alias(client, alias):
    assert post(client, alias=alias).status_code == 422


@pytest.mark.parametrize("alias", ["Mierda123", "PÚTA", "xXfuckXx", "p.u.t.a", "Hijueputa", "sh1t"])
def test_profanity_rejected_with_spanish_message(client, alias):
    r = post(client, alias=alias)
    assert r.status_code == 422
    assert "Alias no permitido" in r.json()["detail"]


@pytest.mark.parametrize("alias", ["Computadora", "Vergara", "Americano", "Niño_Ñu", "Pingüino"])
def test_innocent_aliases_accepted(client, alias):
    assert post(client, alias=alias).status_code == 200


@pytest.mark.parametrize("field", ["run_id", "player_id"])
@pytest.mark.parametrize("bad", ["nope", "123e4567-e89b-12d3-a456-426614174000", 5,
                                 "00000000-0000-0000-0000-000000000000"])
def test_bad_uuid(client, field, bad):
    assert post(client, **{field: bad}).status_code == 422


def test_unknown_fields_rejected(client):
    assert post(client, extra="x").status_code == 422
    body = payload()
    body["components"]["extra"] = 1
    assert client.post("/api/scores", json=body).status_code == 422


def test_invalid_json_and_error_shape(client):
    r = client.post("/api/scores", content=b"{bad", headers={"content-type": "application/json"})
    assert r.status_code == 422 and set(r.json()) == {"error", "detail"}


@pytest.mark.parametrize("duration", [0, 30, 6 * 3600 + 1, 30 * 24 * 3600])
def test_odd_client_duration_is_accepted_unverified(client, duration):
    # Old saves report 0 s and resumed saves report days: never reject, just do not rank.
    r = post(client, duration_s=duration)
    assert r.status_code == 200 and r.json()["verified"] is False


def test_duration_type_bounds(client):
    assert post(client, duration_s=-1).status_code == 422
    assert post(client, duration_s=2**31).status_code == 422


# ---- idempotency / run lifecycle ----------------------------------------

def test_duplicate_is_idempotent(client):
    body = payload()
    first = client.post("/api/scores", json=body).json()
    second = client.post("/api/scores", json=body).json()
    assert first["duplicate"] is False and second["duplicate"] is True
    assert second["rank"] == first["rank"]
    assert client.get("/api/players/" + body["player_id"]).json()["runs"] == 1


def test_duplicate_does_not_overwrite(client):
    body = payload()
    client.post("/api/scores", json=body)
    body.update(with_components(verificacion=300))
    data = client.post("/api/scores", json=body).json()
    assert data["duplicate"] is True and data["personal_best"] == 742


def test_duplicate_with_other_player_conflicts(client):
    body = payload()
    client.post("/api/scores", json=body)
    body["player_id"] = new_id()
    assert client.post("/api/scores", json=body).status_code == 409


def test_queued_resend_hours_later_stays_verified(client, monkeypatch):
    pid = new_id()
    run = start(client, pid, mode="feria")
    advance(monkeypatch, 8 * 3600)  # played 8 min, lost connection, resent next session
    body = payload(run_id=run["run_id"], player_id=pid, mode="feria", duration_s=480)
    first = client.post("/api/scores", json=body)
    assert first.status_code == 200 and first.json()["verified"] is True
    again = client.post("/api/scores", json=body).json()
    assert again["duplicate"] is True and again["verified"] is True


def test_start_then_submit_verified(client, monkeypatch):
    pid = new_id()
    run = start(client, pid)
    assert run["started_at"].endswith("Z")
    advance(monkeypatch, 1700)
    r = post(client, run_id=run["run_id"], player_id=pid, duration_s=1650)
    assert r.status_code == 200 and r.json()["verified"] is True


def test_start_then_too_fast_unverified(client):
    pid = new_id()
    run = start(client, pid)
    r = post(client, run_id=run["run_id"], player_id=pid, duration_s=1650)
    assert r.status_code == 200 and r.json()["verified"] is False


def test_claimed_duration_longer_than_server_time_unverified(client, monkeypatch):
    pid = new_id()
    run = start(client, pid)
    advance(monkeypatch, 1000)
    r = post(client, run_id=run["run_id"], player_id=pid, duration_s=1650)
    assert r.json()["verified"] is False


def test_tolerance_allows_slight_difference(client, monkeypatch):
    pid = new_id()
    run = start(client, pid)
    advance(monkeypatch, 1650 - 100)
    assert post(client, run_id=run["run_id"], player_id=pid,
                duration_s=1650).json()["verified"] is True


@pytest.mark.parametrize("mode,score_kw,play_s,verified", [
    ("feria", dict(verificacion=0), 179, False),         # 502 < 700: needs 180 s
    ("feria", dict(verificacion=0), 180, True),
    ("feria", {}, 299, False),                            # 742 >= 700: needs 300 s
    ("feria", {}, 300, True),
    ("historia", dict(verificacion=0), 599, False),
    ("historia", dict(verificacion=0), 600, True),
    ("historia", {}, 899, False),
    ("historia", {}, 900, True)])
def test_score_vs_server_time(client, monkeypatch, mode, score_kw, play_s, verified):
    pid = new_id()
    run = start(client, pid, mode=mode)
    advance(monkeypatch, play_s)
    r = post(client, run_id=run["run_id"], player_id=pid, mode=mode, duration_s=play_s,
             **with_components(**score_kw))
    assert r.status_code == 200 and r.json()["verified"] is verified


def test_thresholds_configurable(make_client, monkeypatch):
    c = make_client(verify_min_s_feria_high=60)
    pid = new_id()
    run = start(c, pid, mode="feria")
    advance(monkeypatch, 61)
    r = post(c, run_id=run["run_id"], player_id=pid, mode="feria", duration_s=60)
    assert r.json()["verified"] is True


def test_mode_or_platform_mismatch_unverified(client, monkeypatch):
    pid = new_id()
    run_mode = start(client, pid, mode="feria")
    run_plat = start(client, pid, platform="web")
    advance(monkeypatch, 1700)
    assert post(client, run_id=run_mode["run_id"], player_id=pid).json()["verified"] is False
    assert post(client, run_id=run_plat["run_id"], player_id=pid).json()["verified"] is False


def test_expired_run_is_accepted_unverified(client, monkeypatch):
    pid = new_id()
    run = start(client, pid)
    advance(monkeypatch, 24 * 3600 + 5)
    r = post(client, run_id=run["run_id"], player_id=pid)
    assert r.status_code == 200 and r.json()["verified"] is False


def test_started_run_other_player_rejected(client):
    run = start(client, new_id())
    r = post(client, run_id=run["run_id"])
    assert r.status_code == 409 and r.json()["error"] == "run_conflict"


def test_started_run_cannot_be_reused_after_admin_delete(make_client):
    c = make_client(admin_token=ADMIN)
    pid = new_id()
    run = start(c, pid)
    assert post(c, run_id=run["run_id"], player_id=pid).status_code == 200
    c.delete(f"/api/admin/scores/{run['run_id']}", headers={"Authorization": f"Bearer {ADMIN}"})
    r = post(c, run_id=run["run_id"], player_id=pid)
    assert r.status_code == 409 and r.json()["error"] == "run_already_submitted"


def test_start_validation(client):
    r = client.post("/api/runs/start", json={"player_id": "bad", "mode": "historia",
                                              "platform": "pc", "version": "2.0"})
    assert r.status_code == 422


def test_stale_started_runs_are_cleaned(client, monkeypatch):
    store = client.app.state.store
    old = start(client, new_id())
    advance(monkeypatch, 8 * 24 * 3600)
    start(client, new_id())
    assert store.get_run(old["run_id"]) is None


# ---- per-player limits --------------------------------------------------

def test_player_start_limit(make_client):
    c = make_client(rate_player_start_per_hour=2)
    pid, other = new_id(), new_id()
    body = {"player_id": pid, "mode": "feria", "platform": "web", "version": "2.0"}
    codes = [c.post("/api/runs/start", json=body).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
    assert c.post("/api/runs/start", json={**body, "player_id": other}).status_code == 200


def test_player_scores_limit_ignores_resends(make_client):
    c = make_client(rate_player_scores_per_hour=2)
    pid = new_id()
    first = payload(player_id=pid)
    assert c.post("/api/scores", json=first).status_code == 200
    for _ in range(3):
        assert c.post("/api/scores", json=first).status_code == 200  # duplicates are free
    assert post(c, player_id=pid).status_code == 200
    r = post(c, player_id=pid)
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0
    assert post(c).status_code == 200


# ---- ranking ------------------------------------------------------------

def test_best_per_player_and_personal_best(post_verified, client):
    pid = new_id()
    post_verified(player_id=pid, **with_components(verificacion=100))  # 602
    post_verified(player_id=pid, **with_components(verificacion=300))  # 802
    data = post_verified(player_id=pid, **with_components(verificacion=50)).json()  # 552
    assert data["personal_best"] == 802 and data["rank"] == 1
    entries = board(client)
    assert len(entries) == 1 and entries[0]["score"] == 802


def test_ranking_order_and_tiebreak(post_verified, client):
    a, b, c = new_id(), new_id(), new_id()
    post_verified(player_id=a, alias="Primero", **with_components(verificacion=200))
    post_verified(player_id=b, alias="Segundo", **with_components(verificacion=200))
    r = post_verified(player_id=c, alias="Tercero", **with_components(verificacion=300))
    assert r.json()["rank"] == 1
    assert [e["alias"] for e in board(client)] == ["Tercero", "Primero", "Segundo"]
    assert client.get(f"/api/players/{b}").json()["rank"] == 3


def test_leaderboard_modes_and_limit(client):
    for i in range(5):
        post(client, alias=f"Hist{i}", **with_components(verificacion=100 + i))
    for i in range(2):
        post(client, alias=f"Feria{i}", mode="feria", duration_s=900,
             **with_components(verificacion=10 + i))
    q = "&include_unverified=1"
    hist = board(client, "mode=historia" + q)
    feria = board(client, "mode=feria" + q)
    both = board(client, "mode=all&limit=50" + q)
    assert len(hist) == 5 and len(feria) == 2 and len(both) == 7
    assert all(e["mode"] == "historia" for e in hist)
    assert [e["rank"] for e in hist] == [1, 2, 3, 4, 5]
    assert len(board(client, "mode=historia&limit=3" + q)) == 3
    assert len(board(client, "include_unverified=true")) == 7
    assert board(client, "") == []


@pytest.mark.parametrize("qs", ["limit=0", "limit=51", "limit=abc", "mode=zzz",
                                "include_unverified=maybe"])
def test_leaderboard_bad_params(client, qs):
    r = client.get("/api/leaderboard?" + qs)
    assert r.status_code == 422 and set(r.json()) == {"error", "detail"}


def test_same_player_best_per_mode(client):
    pid = new_id()
    post(client, player_id=pid)
    post(client, player_id=pid, mode="feria", duration_s=900)
    assert len(board(client, "mode=all&include_unverified=1")) == 2


# ---- players ------------------------------------------------------------

def test_player_404_and_200(client):
    assert client.get(f"/api/players/{new_id()}").status_code == 404
    assert client.get("/api/players/not-a-uuid").status_code == 404
    pid = new_id()
    post(client, player_id=pid)
    post(client, player_id=pid, final="caos", finales_desbloqueados=["caos"],
         **with_components(ciudad=10))
    data = client.get(f"/api/players/{pid}").json()
    assert data["runs"] == 2 and data["best_final"] == "informada"
    assert data["finales_desbloqueados"] == ["caos", "dividida", "informada"]
    assert data["rank"] == 1 and data["best_score"] == 742 and data["ranked"] is False


# ---- admin --------------------------------------------------------------

@pytest.mark.parametrize("token", ["", "short-token"])
def test_admin_disabled_without_strong_token(make_client, token):
    c = make_client(admin_token=token)
    r = c.delete(f"/api/admin/scores/{new_id()}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_admin_delete(make_client):
    c = make_client(admin_token=ADMIN)
    body = payload()
    c.post("/api/scores", json=body)
    url = f"/api/admin/scores/{body['run_id']}"
    auth = {"Authorization": f"Bearer {ADMIN}"}
    assert c.delete(url).status_code == 401
    assert c.delete(url, headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert c.delete(url, headers=auth).json() == {"deleted": True}
    assert c.delete(url, headers=auth).status_code == 404
    assert board(c, "include_unverified=1") == []


def test_admin_is_rate_limited(make_client):
    c = make_client(admin_token=ADMIN, rate_admin_per_hour=3)
    url = f"/api/admin/scores/{new_id()}"
    codes = [c.delete(url, headers={"Authorization": "Bearer x"}).status_code for _ in range(4)]
    assert codes == [401, 401, 401, 429]
