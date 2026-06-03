# tests/integration/test_auth_flow.py
"""
Integration tests: auth lifecycle — signup → login → refresh → logout.

Requires TEST_DATABASE_URL. All tests run in a rolled-back transaction.
"""

import pytest

SIGNUP_PAYLOAD = {
    "email": "test@example.com",
    "password": "Str0ng!Password#1",
    "username": "testuser",
    "native_lang_id": 1,
}


@pytest.mark.asyncio
async def test_signup_returns_token(client):
    resp = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_409(client):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_valid_credentials_returns_token(client):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": "WrongPassword123!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(client):
    signup = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    refresh_token = signup.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    # Refresh token should be rotated — old token must not be reusable
    assert body.get("refresh_token") != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_reuse_returns_401(client):
    """Replay attack: using a consumed refresh token must fail."""
    signup = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    refresh_token = signup.json()["refresh_token"]

    # Consume the token
    await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    # Replay — must be rejected
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_auth(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token(client):
    signup = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    token = signup.json()["access_token"]

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == SIGNUP_PAYLOAD["email"]
