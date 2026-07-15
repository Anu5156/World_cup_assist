"""Bounded TTL response cache for the assistant.

Keyed on a stable SHA-256 hash of (intent, sorted_needs, language, role,
telemetry_snapshot).  Entries expire after ``ttl_seconds`` and the store
is bounded to ``maxsize`` entries via LRU-style eviction.

Thread-safe via a single ``threading.Lock``.

Usage::

    cache = ResponseCache(maxsize=256, ttl_seconds=120)
    key   = cache.make_key(intent, needs, language, role, stadium_status)
    hit   = cache.get(key)
    if hit is None:
        hit = expensive_call()
        cache.put(key, hit)
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict


class ResponseCache:
    """Thread-safe bounded TTL cache for assistant reply strings."""

    def __init__(self, maxsize: int = 256, ttl_seconds: float = 120.0) -> None:
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        # OrderedDict used as an LRU store: oldest entries at the front.
        self._store: OrderedDict[str, tuple[float, str]] = OrderedDict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def make_key(
        intent: str,
        needs: list[str],
        language: str,
        role: str,
        stadium_status: object | None,
    ) -> str:
        """Return a stable, collision-resistant cache key.

        ``stadium_status`` is serialised with Pydantic's ``model_dump()`` so
        the telemetry snapshot is included in the key without importing the
        full model here.
        """
        status_dict: dict = {}
        if stadium_status is not None and hasattr(stadium_status, "model_dump"):
            status_dict = stadium_status.model_dump()
        payload = json.dumps(
            {
                "intent": intent,
                "needs": sorted(needs),
                "language": language,
                "role": role,
                "status": status_dict,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, key: str) -> str | None:
        """Return the cached reply for *key*, or ``None`` on a miss / expiry."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            # Move to end (most recently used).
            self._store.move_to_end(key)
            return value

    def put(self, key: str, value: str) -> None:
        """Store *value* under *key*, evicting the oldest entry if at capacity."""
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (time.monotonic() + self._ttl, value)
            # Evict oldest entries until we are at or below maxsize.
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def clear(self) -> None:
        """Remove all entries (useful in tests)."""
        with self._lock:
            self._store.clear()
