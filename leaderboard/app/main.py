import hmac
import uuid
from pathlib import Path
from datetime import timedelta
from typing import Literal, Optional

from fastapi import FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import clock
from .config import Settings
from .db import Store
from .ratelimit import RateLimiter
from .schemas import ENDINGS, ScoreSubmission, StartRequest, _uuid4
from .arena_online import crear_router as crear_router_arena

STATIC_DIR = Path(__file__).parent / "static"
RUN_TTL_SECONDS = 24 * 3600
START_TOLERANCE_SECONDS = 120
STALE_RUN_SECONDS = 7 * 24 * 3600
CLEANUP_EVERY_SECONDS = 3600

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"),
}


class ApiError(Exception):
    def __init__(self, status: int, error: str, detail: str, headers: Optional[dict] = None):
        self.status, self.error, self.detail, self.headers = status, error, detail, headers


def error_response(status: int, error: str, detail: str, headers: Optional[dict] = None):
    return JSONResponse({"error": error, "detail": detail}, status_code=status, headers=headers)


def iso(dt) -> str:
    return dt.isoformat(timespec="seconds") + "Z"


def entry_json(row, rank: int) -> dict:
    return {
        "rank": rank, "alias": row["alias"], "score": row["score"], "final": row["final"],
        "final_title": ENDINGS.get(row["final"], row["final"]), "mode": row["mode"],
        "platform": row["platform"], "verified": bool(row["verified"]),
        "created_at": iso(row["created_at"]),
    }


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = Store(settings.database_url)
    limiter = RateLimiter({
        "scores": (settings.rate_scores_per_hour, 3600),
        "start": (settings.rate_start_per_hour, 3600),
        "get": (settings.rate_get_per_min, 60),
        "admin": (settings.rate_admin_per_hour, 3600),
        "player_scores": (settings.rate_player_scores_per_hour, 3600),
        "player_start": (settings.rate_player_start_per_hour, 3600),
        # Arena Online: cada telefono consulta la sala ~1 vez por segundo. Cubo propio para no gastar el
        # del leaderboard (en la feria muchos telefonos comparten una IP publica).
        "arena_get": (6000, 60),
        "arena_accion": (1200, 60),
        "arena_crear": (120, 3600),
    })
    last_cleanup = [clock.utcnow()]
    app = FastAPI(title="Civitas Leaderboard", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store
    app.state.limiter = limiter

    def client_ip(request: Request) -> str:
        if settings.trust_proxy:
            # Render appends to a client-supplied X-Forwarded-For instead of replacing it, so its
            # first hop is spoofable; Cloudflare (in front of Render) overwrites these two.
            for header in ("true-client-ip", "cf-connecting-ip"):
                value = request.headers.get(header, "").strip()
                if value:
                    return value
            forwarded = request.headers.get("x-forwarded-for", "")
            first = forwarded.split(",")[0].strip()
            if first:
                return first
        return request.client.host if request.client else "unknown"

    def rate_limit(bucket: str, key: str) -> None:
        allowed, retry = limiter.check(bucket, key)
        if not allowed:
            raise ApiError(429, "rate_limited", "Demasiadas solicitudes. Intenta mas tarde.",
                           {"Retry-After": str(retry)})

    def top_json(mode: str, limit: int = 10, include_unverified: bool = False) -> list:
        rows = store.leaderboard(mode, limit, verified_only=not include_unverified)
        return [entry_json(r, i + 1) for i, r in enumerate(rows)]

    def score_result(row, duplicate: bool) -> dict:
        pid, mode = row["player_id"], row["mode"]
        best = store.player_best_in_mode(pid, mode, verified_only=False) or row
        public = store.player_best_in_mode(pid, mode, verified_only=True)
        return {
            "accepted": True, "verified": bool(row["verified"]), "duplicate": duplicate,
            "rank": store.rank_of(public or best), "ranked": public is not None,
            "personal_best": best["score"], "top": top_json(mode),
        }

    def is_verified(body: ScoreSubmission, started, age: float) -> bool:
        return (age <= RUN_TTL_SECONDS
                and started["mode"] == body.mode
                and started["platform"] == body.platform
                and body.duration_s <= age + START_TOLERANCE_SECONDS
                and age >= settings.min_play_seconds(body.mode, body.score))

    def cleanup_stale_runs(now) -> None:
        if (now - last_cleanup[0]).total_seconds() < CLEANUP_EVERY_SECONDS:
            return
        last_cleanup[0] = now
        store.delete_stale_runs(now - timedelta(seconds=STALE_RUN_SECONDS))

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        bucket = None
        if request.method == "POST" and path == "/api/scores":
            bucket = "scores"
        elif request.method == "POST" and path == "/api/runs/start":
            bucket = "start"
        elif request.method in ("GET", "HEAD") and path.startswith("/api/arena/"):
            bucket = "arena_get"
        elif request.method in ("GET", "HEAD"):
            bucket = "get"
        elif request.method == "DELETE" and path.startswith("/api/admin/"):
            bucket = "admin"
        if bucket:
            allowed, retry = limiter.check(bucket, client_ip(request))
            if not allowed:
                return error_response(429, "rate_limited",
                                      "Demasiadas solicitudes. Intenta mas tarde.",
                                      {"Retry-After": str(retry)})
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            length = request.headers.get("content-length")
            if length is not None:
                if not length.isdigit() or int(length) > settings.max_body_bytes:
                    return error_response(413, "payload_too_large", "Cuerpo demasiado grande.")
            elif "transfer-encoding" in request.headers:
                return error_response(411, "length_required", "Se requiere Content-Length.")
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response

    if settings.allowed_origins:
        # Added last so it is outermost: 429/413 responses still carry CORS headers.
        app.add_middleware(
            CORSMiddleware, allow_origins=list(settings.allowed_origins),
            allow_methods=["GET", "POST"], allow_headers=["Content-Type"], max_age=600)

    @app.exception_handler(ApiError)
    async def _api_error(_, exc: ApiError):
        return error_response(exc.status, exc.error, exc.detail, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_, exc: RequestValidationError):
        parts = []
        for err in exc.errors()[:3]:
            field = ".".join(str(p) for p in err["loc"] if p not in ("body", "query", "path"))
            msg = err["msg"].removeprefix("Value error, ")
            parts.append(f"{field}: {msg}" if field else msg)
        return error_response(422, "validation_error", " | ".join(parts) or "Solicitud invalida.")

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_, exc: StarletteHTTPException):
        codes = {404: "not_found", 405: "method_not_allowed"}
        return error_response(exc.status_code, codes.get(exc.status_code, "http_error"),
                              str(exc.detail), getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def _unhandled(_, exc: Exception):
        return error_response(500, "internal_error", "Error interno del servidor.")

    @app.get("/api/health")
    def health(db: int = 0):
        # ?db=1 comprueba la base de datos. El health check de Render no lo usa: despertaria
        # a Neon cada pocos segundos y gastaria sus horas gratuitas.
        if not db:
            return {"ok": True}
        if not store.ping():
            return error_response(503, "db_unavailable", "La base de datos no responde.")
        return {"ok": True, "db": "ok"}

    @app.post("/api/runs/start")
    def start_run(body: StartRequest):
        rate_limit("player_start", body.player_id)
        run_id, now = str(uuid.uuid4()), clock.utcnow()
        cleanup_stale_runs(now)
        store.create_run(run_id, body.player_id, body.mode, body.platform, body.version, now)
        return {"run_id": run_id, "started_at": iso(now)}

    @app.post("/api/scores")
    def submit_score(body: ScoreSubmission):
        existing = store.get_score(body.run_id)
        if existing:
            if existing["player_id"] != body.player_id:
                raise ApiError(409, "run_conflict", "El run_id pertenece a otro jugador.")
            return score_result(existing, duplicate=True)

        rate_limit("player_scores", body.player_id)
        now = clock.utcnow()
        verified = False
        started = store.get_run(body.run_id)
        if started:
            if started["player_id"] != body.player_id:
                raise ApiError(409, "run_conflict", "El run_id pertenece a otro jugador.")
            if started["used"]:
                raise ApiError(409, "run_already_submitted", "Esta partida ya fue enviada.")
            # An expired run (e.g. a save resumed days later) is stored but unverified:
            # rejecting it would lose a real result and gains nothing over not ranking it.
            verified = is_verified(body, started, (now - started["started_at"]).total_seconds())

        row = {
            "run_id": body.run_id, "player_id": body.player_id, "alias": body.alias,
            "platform": body.platform, "mode": body.mode, "final": body.final,
            "score": body.score, "components": body.components.model_dump(),
            "evidencias": body.evidencias, "duration_s": body.duration_s,
            "finales": body.finales_desbloqueados, "version": body.version,
            "verified": verified, "created_at": now,
        }
        if not store.insert_score(row):
            return score_result(store.get_score(body.run_id), duplicate=True)
        return score_result(row, duplicate=False)

    @app.get("/api/leaderboard")
    def leaderboard(mode: Literal["historia", "feria", "all"] = "all",
                    limit: int = Query(10, ge=1, le=50), include_unverified: bool = False):
        return {"entries": top_json(mode, limit, include_unverified)}

    @app.get("/api/players/{player_id}")
    def player(player_id: str):
        try:
            player_id = _uuid4(player_id)
        except ValueError:
            raise ApiError(404, "not_found", "Jugador no encontrado.")
        summary = store.player_summary(player_id)
        if not summary:
            raise ApiError(404, "not_found", "Jugador no encontrado.")
        best = summary["best"]
        public = store.player_best_in_mode(player_id, best["mode"], verified_only=True)
        return {
            "best_score": best["score"], "best_final": best["final"], "runs": summary["runs"],
            "finales_desbloqueados": sorted(summary["finales"]),
            "rank": store.rank_of(public or best), "ranked": public is not None,
        }

    @app.delete("/api/admin/scores/{run_id}")
    def admin_delete(run_id: str, authorization: Optional[str] = Header(None)):
        token = settings.admin_token
        if not settings.admin_enabled:
            raise ApiError(404, "not_found", "No encontrado.")
        supplied = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        if not hmac.compare_digest(supplied.encode(), token.encode()):
            raise ApiError(401, "unauthorized", "Token invalido.",
                           {"WWW-Authenticate": "Bearer"})
        if not store.delete_score(run_id):
            raise ApiError(404, "not_found", "Puntuacion no encontrada.")
        return {"deleted": True}

    router_arena = crear_router_arena(ApiError, rate_limit, client_ip)
    app.state.arena = router_arena.arena
    app.include_router(router_arena)

    @app.get("/arena", include_in_schema=False)
    def arena_online():
        return FileResponse(STATIC_DIR / "arena.html", media_type="text/html")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def __getattr__(name: str):
    # Lazy so importing this module (tests) does not create a database.
    if name == "app":
        instance = create_app()
        globals()["app"] = instance
        return instance
    raise AttributeError(name)
