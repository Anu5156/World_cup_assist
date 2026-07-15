"""Tests for the ResponseCache (src/stadium_assistant/cache.py)."""

from __future__ import annotations

import time

from stadium_assistant.cache import ResponseCache


def _key(cache: ResponseCache, suffix: str = "a") -> str:
    return cache.make_key(
        intent="accessibility",
        needs=["mobility"],
        language="en",
        role="fan",
        stadium_status=None,
    )


# ─── Basic miss / put / hit ───────────────────────────────────────────────────

def test_cache_miss() -> None:
    cache = ResponseCache()
    assert cache.get("no-such-key") is None


def test_cache_put_then_hit() -> None:
    cache = ResponseCache()
    key = _key(cache)
    cache.put(key, "hello")
    assert cache.get(key) == "hello"


def test_make_key_is_deterministic() -> None:
    cache = ResponseCache()
    k1 = cache.make_key("accessibility", ["mobility"], "en", "fan", None)
    k2 = cache.make_key("accessibility", ["mobility"], "en", "fan", None)
    assert k1 == k2


def test_make_key_differs_on_needs_order() -> None:
    """sorted(needs) means order doesn't matter — same key."""
    cache = ResponseCache()
    k1 = cache.make_key("nav", ["hearing", "mobility"], "en", "fan", None)
    k2 = cache.make_key("nav", ["mobility", "hearing"], "en", "fan", None)
    assert k1 == k2


def test_make_key_differs_on_language() -> None:
    cache = ResponseCache()
    k1 = cache.make_key("nav", [], "en", "fan", None)
    k2 = cache.make_key("nav", [], "es", "fan", None)
    assert k1 != k2


# ─── TTL expiry ───────────────────────────────────────────────────────────────

def test_cache_expires_after_ttl() -> None:
    cache = ResponseCache(ttl_seconds=0.05)   # 50 ms TTL
    key = _key(cache)
    cache.put(key, "expires-soon")
    assert cache.get(key) == "expires-soon"
    time.sleep(0.1)                           # wait past TTL
    assert cache.get(key) is None


# ─── Maxsize eviction ─────────────────────────────────────────────────────────

def test_cache_evicts_oldest_on_overflow() -> None:
    cache = ResponseCache(maxsize=3, ttl_seconds=60)
    for i in range(3):
        cache.put(f"key-{i}", f"value-{i}")
    # All three should hit
    for i in range(3):
        assert cache.get(f"key-{i}") == f"value-{i}"

    # Adding a 4th entry evicts the LRU (key-0)
    cache.put("key-3", "value-3")
    assert cache.get("key-0") is None
    assert cache.get("key-3") == "value-3"


def test_cache_clear() -> None:
    cache = ResponseCache()
    key = _key(cache)
    cache.put(key, "to-be-cleared")
    cache.clear()
    assert cache.get(key) is None
