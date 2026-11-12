from tests.conftest import new_id, payload

ORIGIN = "https://game.example.com"


def test_rate_limit_scores_429(make_client):
    c = make_client(rate_scores_per_hour=8)
    codes = [c.post("/api/scores", json=payload()).status_code for _ in range(9)]
    assert codes[:8] == [200] * 8 and codes[8] == 429
    r = c.post("/api/scores", json=payload())
    assert int(r.headers["retry-after"]) > 0
    assert set(r.json()) == {"error", "detail"}


def test_rate_limit_start_and_get(make_client):
    c = make_client(rate_start_per_hour=2, rate_get_per_min=3)
    body = {"player_id": new_id(), "mode": "feria", "platform": "web", "version": "2.0"}
    assert [c.post("/api/runs/start", json=body).status_code for _ in range(3)] == [200, 200, 429]
    assert [c.get("/api/health").status_code for _ in range(4)] == [200, 200, 200, 429]


def test_rate_limit_invalid_requests_count(make_client):
    c = make_client(rate_scores_per_hour=2)
    codes = [c.post("/api/scores", json={}).status_code for _ in range(3)]
    assert codes == [422, 422, 429]


def test_xff_ignored_without_trust_proxy(make_client):
    c = make_client(rate_get_per_min=2)
    codes = [c.get("/api/health", headers={"X-Forwarded-For": f"1.1.1.{i}"}).status_code
             for i in range(3)]
    assert codes == [200, 200, 429]


def test_xff_first_hop_with_trust_proxy(make_client):
    c = make_client(rate_get_per_min=2, trust_proxy=True)

    def h(ip):
        return {"X-Forwarded-For": f"{ip}, 10.0.0.1"}

    assert [c.get("/api/health", headers=h("1.1.1.1")).status_code for _ in range(3)] == [200, 200, 429]
    assert c.get("/api/health", headers=h("2.2.2.2")).status_code == 200


def test_body_too_large_413(client):
    r = client.post("/api/scores", json=payload(alias="a" * 5000))
    assert r.status_code == 413 and set(r.json()) == {"error", "detail"}


def test_normal_body_is_processed(client):
    assert client.post("/api/scores", json=payload()).status_code == 200


def test_cors_without_origin_works(client):
    r = client.post("/api/scores", json=payload())
    assert r.status_code == 200 and "access-control-allow-origin" not in r.headers


def test_cors_wildcard_in_development(client):
    r = client.get("/api/health", headers={"Origin": ORIGIN})
    assert r.headers["access-control-allow-origin"] == "*"


def test_cors_preflight(client):
    r = client.options("/api/scores", headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert r.status_code == 200
    assert "POST" in r.headers["access-control-allow-methods"]
    assert "content-type" in r.headers["access-control-allow-headers"].lower()


def test_cors_production_default_blocks_browsers_but_not_desktop(make_client):
    c = make_client(env="production", allowed_origins=())
    r = c.get("/api/health", headers={"Origin": ORIGIN})
    assert "access-control-allow-origin" not in r.headers
    assert c.get("/api/health").status_code == 200


def test_cors_allowlist(make_client):
    c = make_client(allowed_origins=(ORIGIN,))
    ok = c.get("/api/health", headers={"Origin": ORIGIN})
    assert ok.headers["access-control-allow-origin"] == ORIGIN
    bad = c.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


def test_cors_headers_on_429(make_client):
    c = make_client(allowed_origins=(ORIGIN,), rate_get_per_min=1)
    c.get("/api/health")
    r = c.get("/api/health", headers={"Origin": ORIGIN})
    assert r.status_code == 429 and r.headers["access-control-allow-origin"] == ORIGIN


def test_settings_from_env(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    assert Settings.from_env().allowed_origins == ()
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.com/, https://b.com")
    assert Settings.from_env().allowed_origins == ("https://a.com", "https://b.com")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("ALLOWED_ORIGINS")
    assert Settings.from_env().allowed_origins == ("*",)


def test_postgres_url_normalized():
    from app.db import normalize_url
    assert normalize_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_url("postgresql://u:p@h/db?sslmode=require").startswith("postgresql+psycopg://")
    assert normalize_url("sqlite:///x.db") == "sqlite:///x.db"


def test_no_stack_in_error_responses(client):
    r = client.post("/api/scores", content=b"[]", headers={"content-type": "application/json"})
    assert r.status_code == 422 and "Traceback" not in r.text


def test_cloudflare_client_ip_preferred_over_spoofable_xff(make_client):
    c = make_client(rate_get_per_min=2, trust_proxy=True)

    def h(spoof):
        return {"X-Forwarded-For": f"{spoof}, 10.0.0.1", "True-Client-IP": "3.3.3.3"}

    codes = [c.get("/api/health", headers=h(f"9.9.9.{i}")).status_code for i in range(3)]
    assert codes == [200, 200, 429]
    assert c.get("/api/health", headers={"CF-Connecting-IP": "4.4.4.4"}).status_code == 200


def test_production_never_allows_wildcard(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*, https://ac020907.github.io")
    assert Settings.from_env().allowed_origins == ("https://ac020907.github.io",)


def test_github_pages_origin_in_production(make_client):
    origin = "https://ac020907.github.io"
    c = make_client(env="production", allowed_origins=(origin,))
    r = c.options("/api/scores", headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                                          "Access-Control-Request-Headers": "content-type"})
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == origin
    r = c.get("/api/health", headers={"Origin": "https://evil.github.io"})
    assert "access-control-allow-origin" not in r.headers


def test_unhandled_error_is_generic_json(make_client):
    from fastapi.testclient import TestClient
    app = make_client().app

    def boom(*_a, **_k):
        raise RuntimeError("db password=hunter2 at line 42")

    app.state.store.leaderboard = boom
    r = TestClient(app, raise_server_exceptions=False).get("/api/leaderboard")
    assert r.status_code == 500 and r.json() == {"error": "internal_error",
                                                  "detail": "Error interno del servidor."}
    assert "hunter2" not in r.text


def test_chunked_body_without_length_rejected(client):
    def gen():
        yield b"{}"

    r = client.post("/api/scores", content=gen(), headers={"content-type": "application/json"})
    assert r.status_code == 411


def test_no_string_built_sql():
    import re
    from pathlib import Path
    source = (Path(__file__).parents[1] / "app" / "db.py").read_text(encoding="utf-8")
    assert not re.search(r"\btext\(|execute\(\s*f?[\"']", source)
