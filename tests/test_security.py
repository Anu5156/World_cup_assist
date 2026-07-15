"""Tests for security controls: authentication, proxy IP checks, rate limits, and headers."""

import pytest
from fastapi.testclient import TestClient

from stadium_assistant import app as app_mod
from stadium_assistant.app import _resolve_client_ip, app
from stadium_assistant.config import Settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_security_headers_present(client: TestClient) -> None:
    """Verify standard security headers and CSP are returned on every endpoint."""
    res = client.get("/health")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert res.headers["X-Frame-Options"] == "DENY"
    csp = res.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com" in csp
    assert "font-src 'self' https://fonts.gstatic.com" in csp


def test_status_get_is_public(client: TestClient) -> None:
    """Verify GET /api/stadium/status does not require ops auth."""
    res = client.get("/api/stadium/status")
    assert res.status_code == 200


def test_status_post_requires_auth(client: TestClient) -> None:
    """Verify POST /api/stadium/status checks authentication and fails closed."""
    payload = {
        "gate_congestion": {"A": "Low", "B": "Low", "C": "Low", "D": "Low"},
        "elevator_status": {"A": "Online", "B": "Online", "C": "Online", "D": "Online"},
        "transit_status": "On Time",
        "concession_times": "Normal",
        "sensory_room_occupancy": "Open",
        "active_alert": None,
    }

    # 1. No header -> 401
    res = client.post("/api/stadium/status", json=payload)
    assert res.status_code == 401

    # 2. Bad header -> 401
    res = client.post("/api/stadium/status", json=payload, headers={"X-Ops-Key": "wrongkey"})
    assert res.status_code == 401

    # 3. Correct header -> 200 (using "testkey" configured in conftest.py)
    res = client.post("/api/stadium/status", json=payload, headers={"X-Ops-Key": "testkey"})
    assert res.status_code == 200

    # 4. If OPS_API_KEY is unset, reject all writes (Fail closed)
    app_mod.settings = Settings(ops_api_key="", allowed_origins="*")
    res = client.post("/api/stadium/status", json=payload, headers={"X-Ops-Key": ""})
    assert res.status_code == 401
    res = client.post("/api/stadium/status", json=payload, headers={"X-Ops-Key": "testkey"})
    assert res.status_code == 401


def test_proxy_client_ip_resolution(client: TestClient) -> None:
    """Verify TRUST_PROXY settings read X-Forwarded-For leftmost entry."""
    # When TRUST_PROXY is True (set in conftest.py)
    app_mod.settings = Settings(trust_proxy=True, ops_api_key="testkey")
    
    # Leftmost entry is extracted
    assert client.get("/health", headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}).status_code == 200
    # Let's inspect proxy resolver directly since health check doesn't return client IP
    from fastapi import Request
    # Create a mock Request object
    req = Request(
        scope={
            "type": "http",
            "headers": [(b"x-forwarded-for", b"1.2.3.4, 5.6.7.8")],
            "client": ("127.0.0.1", 1234),
        }
    )
    assert _resolve_client_ip(req) == "1.2.3.4"

    # When TRUST_PROXY is False
    app_mod.settings = Settings(trust_proxy=False, ops_api_key="testkey")
    assert _resolve_client_ip(req) == "127.0.0.1"


def test_rate_limiter_evicts_old_entries(client: TestClient) -> None:
    """Verify rate limiter does not leak memory or lock out clients permanently."""
    # Set limit to 2 requests per window to test quickly
    app_mod.settings = Settings(
        rate_limit_requests=2,
        rate_limit_window_seconds=1,
        ops_api_key="testkey",
    )
    
    # Reset hits dict
    from stadium_assistant.app import _hits
    _hits.clear()

    # Request 1 -> 200
    res = client.get("/health")
    assert res.status_code == 200

    # Request 2 -> 200 (matches rate_limit_requests=2 limit)
    res = client.get("/health")
    # Wait, /health is GET and not rate limited in assist but update status and assist are limited.
    # Ah, let's call assist instead of health!
    res = client.post("/api/assist", json={"message": "hello"})
    assert res.status_code == 200

    res = client.post("/api/assist", json={"message": "hello"})
    assert res.status_code == 200

    # Request 3 -> 429
    res = client.post("/api/assist", json={"message": "hello"})
    assert res.status_code == 429

    # Verify global sweep logic triggers when keys exceed 1000
    for i in range(1005):
        _hits[f"ip-{i}"].append(0.0) # expired timestamps
    
    assert len(_hits) > 1000
    # Next rate limit check should trigger sweep and evict all expired IPs
    res = client.post("/api/assist", json={"message": "hello"})
    # Since keys exceeded 1000, empty/expired entries are swept
    assert len(_hits) < 100
