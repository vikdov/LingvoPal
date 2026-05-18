# tests/integration/test_lockout.py
"""
Integration tests: login brute-force lockout.

Verifies that 10 consecutive wrong-password attempts lock the account,
and that concurrent attempts don't allow unbounded bypass.
"""

import asyncio
import pytest


SIGNUP_PAYLOAD = {
    "email": "locktest@example.com",
    "password": "Str0ng!Password#1",
    "username": "lockuser",
    "native_lang_id": 1,
}

WRONG_PASSWORD = "WrongPassword99!"


@pytest.mark.asyncio
async def test_lockout_triggers_after_10_failures(client):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    for i in range(10):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": SIGNUP_PAYLOAD["email"], "password": WRONG_PASSWORD},
        )
        assert resp.status_code == 401, f"Attempt {i + 1} should return 401"

    # 11th attempt — must be locked out
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    assert resp.status_code in (401, 423), (
        f"Expected lockout (401/423) after 10 failures, got {resp.status_code}"
    )


@pytest.mark.asyncio
async def test_successful_login_clears_fail_counter(client):
    """Correct login resets the counter so legitimate users aren't locked out."""
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    # 5 failures (below threshold)
    for _ in range(5):
        await client.post(
            "/api/v1/auth/login",
            json={"email": SIGNUP_PAYLOAD["email"], "password": WRONG_PASSWORD},
        )

    # Correct login — must succeed and clear counter
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    assert resp.status_code == 200, "Correct login after 5 failures must succeed"

    # 5 more failures after reset — still under threshold
    for _ in range(5):
        await client.post(
            "/api/v1/auth/login",
            json={"email": SIGNUP_PAYLOAD["email"], "password": WRONG_PASSWORD},
        )

    # Correct login again — must still succeed (counter was reset)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_failed_attempts_lockout(client):
    """
    Fire 15 bad login attempts concurrently.
    After they all resolve, the account must be locked — no unbounded bypass.
    """
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    attempts = [
        client.post(
            "/api/v1/auth/login",
            json={"email": SIGNUP_PAYLOAD["email"], "password": WRONG_PASSWORD},
        )
        for _ in range(15)
    ]
    results = await asyncio.gather(*attempts)
    status_codes = [r.status_code for r in results]

    # All failed (401 or locked 423) — no 200
    assert all(c in (401, 423) for c in status_codes), (
        f"Concurrent attempts returned unexpected statuses: {status_codes}"
    )

    # Account must now be locked
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    assert resp.status_code in (401, 423), "Account must be locked after 15 concurrent failures"
