import json
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Integer, MetaData, String, Table,
                        create_engine, delete, func, insert, literal, select, update)
from sqlalchemy.exc import IntegrityError

metadata = MetaData()

started_runs = Table(
    "started_runs", metadata,
    Column("run_id", String(36), primary_key=True),
    Column("player_id", String(36), nullable=False),
    Column("mode", String(10), nullable=False),
    Column("platform", String(10), nullable=False),
    Column("version", String(20), nullable=False),
    Column("started_at", DateTime, nullable=False),
    Column("used", Boolean, nullable=False, default=False),
)

scores = Table(
    "scores", metadata,
    Column("run_id", String(36), primary_key=True),
    Column("player_id", String(36), nullable=False, index=True),
    Column("alias", String(20), nullable=False),
    Column("platform", String(10), nullable=False),
    Column("mode", String(10), nullable=False),
    Column("final", String(12), nullable=False),
    Column("score", Integer, nullable=False),
    Column("components", JSON, nullable=False),
    Column("evidencias", Integer, nullable=False),
    Column("duration_s", Integer, nullable=False),
    Column("finales", JSON, nullable=False),
    Column("version", String(20), nullable=False),
    Column("verified", Boolean, nullable=False),
    Column("created_at", DateTime, nullable=False),
)

_ORDER = (scores.c.score.desc(), scores.c.created_at.asc(), scores.c.run_id.asc())


def normalize_url(url: str) -> str:
    # Neon/Supabase hand out postgres:// or postgresql://; SQLAlchemy needs the psycopg 3 driver name.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Store:
    def __init__(self, url: str):
        url = normalize_url(url)
        kwargs = {} if url.startswith("sqlite") else {"pool_pre_ping": True}
        self.engine = create_engine(url, **kwargs)
        metadata.create_all(self.engine)

    def ping(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(select(literal(1)))
            return True
        except Exception:
            return False

    def _best(self, mode: str, verified_only: bool):
        """Best run per (player, mode); ties go to the earlier submission."""
        rn = func.row_number().over(
            partition_by=[scores.c.player_id, scores.c.mode], order_by=_ORDER).label("rn")
        query = select(scores, rn)
        if mode != "all":
            query = query.where(scores.c.mode == mode)
        if verified_only:
            query = query.where(scores.c.verified.is_(True))
        return query.subquery("ranked")

    def create_run(self, run_id, player_id, mode, platform, version, started_at: datetime):
        with self.engine.begin() as conn:
            conn.execute(insert(started_runs).values(
                run_id=run_id, player_id=player_id, mode=mode, platform=platform,
                version=version, started_at=started_at, used=False))

    def get_run(self, run_id):
        with self.engine.connect() as conn:
            return conn.execute(
                select(started_runs).where(started_runs.c.run_id == run_id)).mappings().first()

    def get_score(self, run_id):
        with self.engine.connect() as conn:
            return conn.execute(select(scores).where(scores.c.run_id == run_id)).mappings().first()

    def insert_score(self, row: dict) -> bool:
        """Returns False when run_id already has a score (lost an idempotency race)."""
        try:
            with self.engine.begin() as conn:
                conn.execute(insert(scores).values(**row))
                conn.execute(update(started_runs).where(started_runs.c.run_id == row["run_id"])
                             .values(used=True))
        except IntegrityError:
            return False
        return True

    def delete_stale_runs(self, older_than: datetime) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(started_runs).where(started_runs.c.started_at < older_than))

    def delete_score(self, run_id) -> bool:
        with self.engine.begin() as conn:
            return conn.execute(delete(scores).where(scores.c.run_id == run_id)).rowcount > 0

    def leaderboard(self, mode: str, limit: int, verified_only: bool = True):
        best = self._best(mode, verified_only)
        query = (select(best).where(best.c.rn == 1)
                 .order_by(best.c.score.desc(), best.c.created_at.asc(), best.c.run_id.asc())
                 .limit(limit))
        with self.engine.connect() as conn:
            return list(conn.execute(query).mappings())

    def player_best_in_mode(self, player_id: str, mode: str, verified_only: bool):
        best = self._best(mode, verified_only)
        with self.engine.connect() as conn:
            return conn.execute(select(best).where(
                best.c.rn == 1, best.c.player_id == player_id)).mappings().first()

    def rank_of(self, row) -> int:
        """Position of row within the public (verified) ranking of its mode; for an unverified
        row this is the position it would have, counting only other players' entries."""
        best = self._best(row["mode"], verified_only=True)
        ahead = ((best.c.score > row["score"])
                 | ((best.c.score == row["score"]) & (best.c.created_at < row["created_at"]))
                 | ((best.c.score == row["score"]) & (best.c.created_at == row["created_at"])
                    & (best.c.run_id < row["run_id"])))
        with self.engine.connect() as conn:
            return conn.execute(
                select(func.count()).select_from(best).where(
                    best.c.rn == 1, best.c.player_id != row["player_id"], ahead)).scalar() + 1

    def player_summary(self, player_id: str):
        with self.engine.connect() as conn:
            rows = list(conn.execute(select(scores).where(scores.c.player_id == player_id)
                                     .order_by(*_ORDER)).mappings())
        if not rows:
            return None
        unlocked = set()
        for r in rows:
            f = r["finales"]
            unlocked.update(json.loads(f) if isinstance(f, str) else f)
        return {"best": rows[0], "runs": len(rows), "finales": unlocked}
