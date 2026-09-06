import uuid

import httpx

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from tests.conftest import ATTORNEY_EMAIL, ATTORNEY_PASSWORD, TEST_SECRET


async def test_login_sets_cookie_and_logout_clears_it(
    client: httpx.AsyncClient, attorney: User
) -> None:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json() == {"id": str(attorney.id), "email": ATTORNEY_EMAIL}
    cookie = resp.headers["set-cookie"]
    assert (
        "access_token=" in cookie
        and "HttpOnly" in cookie
        and "SameSite=lax" in cookie.replace("samesite", "SameSite")
    )

    assert (await client.get("/api/v1/auth/me")).status_code == 200

    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    assert 'access_token=""' in resp.headers["set-cookie"]
    client.cookies.clear()
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_login_rejects_bad_credentials(client: httpx.AsyncClient, attorney: User) -> None:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": "wrong"}
    )
    assert resp.status_code == 401
    assert "set-cookie" not in resp.headers
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "x"}
    )
    assert resp.status_code == 401


async def test_bearer_header_is_accepted(client: httpx.AsyncClient, attorney: User) -> None:
    token = create_access_token(attorney.id, secret=TEST_SECRET, expires_minutes=5)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


async def test_logout_requires_auth(client: httpx.AsyncClient) -> None:
    assert (await client.post("/api/v1/auth/logout")).status_code == 401


def test_password_and_token_helpers() -> None:
    hashed = hash_password("secret")
    assert hashed.startswith("$2b$") and verify_password("secret", hashed)
    assert not verify_password("other", hashed)
    assert not verify_password("secret", "not-a-hash")

    secret = "x" * 32
    user_id = uuid.uuid4()
    token = create_access_token(user_id, secret=secret, expires_minutes=1)
    assert decode_access_token(token, secret=secret) == user_id
    assert decode_access_token(token, secret="y" * 32) is None
    expired = create_access_token(user_id, secret=secret, expires_minutes=-1)
    assert decode_access_token(expired, secret=secret) is None
