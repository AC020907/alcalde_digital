import os
from dataclasses import dataclass

MIN_ADMIN_TOKEN_LENGTH = 16


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./leaderboard.db"
    env: str = "development"
    allowed_origins: tuple = ()
    trust_proxy: bool = False
    admin_token: str = ""
    # Per client IP. At the fair many phones share one public IP, so keep these generous.
    rate_scores_per_hour: int = 60
    rate_start_per_hour: int = 120
    rate_get_per_min: int = 120
    rate_admin_per_hour: int = 30
    # Per player_id: the real per-person brake.
    rate_player_scores_per_hour: int = 20
    rate_player_start_per_hour: int = 20
    max_body_bytes: int = 4096
    # Verification: minimum server-measured play time (seconds) per mode, and a stricter
    # minimum for scores >= verify_high_score.
    verify_high_score: int = 700
    verify_min_s_feria: int = 180
    verify_min_s_feria_high: int = 300
    verify_min_s_historia: int = 600
    verify_min_s_historia_high: int = 900

    @property
    def admin_enabled(self) -> bool:
        return len(self.admin_token) >= MIN_ADMIN_TOKEN_LENGTH

    def min_play_seconds(self, mode: str, score: int) -> int:
        high = score >= self.verify_high_score
        if mode == "feria":
            return self.verify_min_s_feria_high if high else self.verify_min_s_feria
        return self.verify_min_s_historia_high if high else self.verify_min_s_historia

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ.get("ENV", "development").lower()
        raw = os.environ.get("ALLOWED_ORIGINS", "").strip()
        if raw:
            origins = tuple(o.strip().rstrip("/") for o in raw.split(",") if o.strip())
        else:
            origins = ("*",) if env != "production" else ()
        if env == "production":
            origins = tuple(o for o in origins if o != "*")
        d = cls()
        return cls(
            database_url=os.environ.get("DATABASE_URL", "").strip() or d.database_url,
            env=env,
            allowed_origins=origins,
            trust_proxy=os.environ.get("TRUST_PROXY", "0") == "1",
            admin_token=os.environ.get("ADMIN_TOKEN", "").strip(),
            rate_scores_per_hour=_int("RATE_SCORES_PER_HOUR", d.rate_scores_per_hour),
            rate_start_per_hour=_int("RATE_START_PER_HOUR", d.rate_start_per_hour),
            rate_get_per_min=_int("RATE_GET_PER_MIN", d.rate_get_per_min),
            rate_admin_per_hour=_int("RATE_ADMIN_PER_HOUR", d.rate_admin_per_hour),
            rate_player_scores_per_hour=_int("RATE_PLAYER_SCORES_PER_HOUR",
                                             d.rate_player_scores_per_hour),
            rate_player_start_per_hour=_int("RATE_PLAYER_START_PER_HOUR",
                                            d.rate_player_start_per_hour),
            verify_high_score=_int("VERIFY_HIGH_SCORE", d.verify_high_score),
            verify_min_s_feria=_int("VERIFY_MIN_S_FERIA", d.verify_min_s_feria),
            verify_min_s_feria_high=_int("VERIFY_MIN_S_FERIA_HIGH", d.verify_min_s_feria_high),
            verify_min_s_historia=_int("VERIFY_MIN_S_HISTORIA", d.verify_min_s_historia),
            verify_min_s_historia_high=_int("VERIFY_MIN_S_HISTORIA_HIGH",
                                            d.verify_min_s_historia_high),
        )
