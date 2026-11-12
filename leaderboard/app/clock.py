from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC datetime; module-level so tests can monkeypatch it."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
