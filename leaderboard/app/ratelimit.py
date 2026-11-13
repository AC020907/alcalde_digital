import hashlib
import os
import threading
import time


class RateLimiter:
    """In-process token bucket per (bucket name, hashed client key)."""

    def __init__(self, limits: dict, clock=time.monotonic):
        # limits: name -> (capacity, period_seconds)
        self.limits = limits
        self.clock = clock
        self._salt = os.urandom(16)
        self._state: dict = {}
        self._lock = threading.Lock()

    def hash_key(self, raw: str) -> str:
        return hashlib.sha256(self._salt + raw.encode()).hexdigest()[:24]

    def check(self, name: str, client: str):
        """Returns (allowed, retry_after_seconds)."""
        capacity, period = self.limits[name]
        rate = capacity / period
        key = (name, self.hash_key(client))
        now = self.clock()
        with self._lock:
            tokens, last = self._state.get(key, (float(capacity), now))
            tokens = min(float(capacity), tokens + (now - last) * rate)
            if tokens >= 1:
                self._state[key] = (tokens - 1, now)
                allowed, retry = True, 0
            else:
                self._state[key] = (tokens, now)
                allowed, retry = False, int((1 - tokens) / rate) + 1
            if len(self._state) > 20000:
                self._evict(now)
        return allowed, retry

    def _evict(self, now: float) -> None:
        # Buckets idle long enough to be full again carry no information.
        for key in list(self._state):
            capacity, period = self.limits[key[0]]
            tokens, last = self._state[key]
            if tokens + (now - last) * capacity / period >= capacity:
                del self._state[key]
