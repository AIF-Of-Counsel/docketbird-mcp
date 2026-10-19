"""Tests for the ASGI router in docketbird_mcp.py (`app`).

Drives `docketbird_mcp.app` directly with hand-rolled ASGI scope/receive/send
(no real server). Covers: /health is exempt from rate limiting, the rate
limiter itself returns 429 once exceeded, and basic path dispatch to the
custom auth routes.
"""

import os

os.environ.setdefault("DATA_DIR", "/tmp/docketbird-test-data")

import json
import time

import pytest

import docketbird_mcp as d
from auth_provider import DocketBirdAccessToken


async def _call_app(path: str, client_ip: str, method: str = "GET", headers=()):
    """Drive `d.app` for a single HTTP request and collect the response."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": list(headers),
        "query_string": b"",
        "client": (client_ip, 12345),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    messages = []

    async def send(message):
        messages.append(message)

    await d.app(scope, receive, send)

    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    status = start["status"]
    return status, body


@pytest.fixture(autouse=True)
def _fresh_rate_limiter(monkeypatch):
    """Isolate each test from the module-global rate limiter."""
    monkeypatch.setattr(d, "rate_limiter", d.RateLimiter(d.RATE_LIMIT_REQUESTS, d.RATE_LIMIT_WINDOW))


@pytest.mark.asyncio
async def test_health_ok_and_not_rate_limited():
    for _ in range(40):
        status, body = await _call_app("/health", "10.1.1.1")
        assert status == 200
        assert json.loads(body)["status"] == "ok"


@pytest.mark.asyncio
async def test_rate_limit_returns_429_after_threshold():
    ip = "10.9.9.9"
    statuses = []
    for _ in range(31):
        status, _ = await _call_app("/login", ip)
        statuses.append(status)
    assert statuses[-1] == 429
    assert all(s == 200 for s in statuses[:30])


@pytest.mark.asyncio
async def test_signup_path_dispatch():
    status, body = await _call_app("/signup", "10.2.2.2")
    assert status == 200
    assert b"Create Account" in body


async def _seed_token(auth_db, resource):
    uid = await auth_db.create_user("aud@example.com", "password123", "k")
    await auth_db.save_access_token(
        DocketBirdAccessToken(
            token="acc-aud",
            client_id="client-abc",
            scopes=["docketbird"],
            expires_at=int(time.time() + 3600),
            resource=resource,
            docketbird_api_key="k",
            user_id=uid,
        )
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("resource", "expect_401"),
    [(f"{d.SERVER_URL}/mcp", False), (None, False), ("https://other.example.com/mcp", True)],
)
async def test_mcp_bearer_resource_check(monkeypatch, auth_db, resource, expect_401):
    monkeypatch.setattr(d.auth_provider, "db", auth_db)

    async def _ok(scope, receive, send):  # stands in for the MCP session manager behind the auth check
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    monkeypatch.setattr(d.mcp.session_manager, "handle_request", _ok)
    await _seed_token(auth_db, resource)
    status, _ = await _call_app("/mcp", "10.3.3.3", "POST", [(b"authorization", b"Bearer acc-aud")])
    assert status == (401 if expect_401 else 200)
