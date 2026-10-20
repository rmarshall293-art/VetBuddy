"""Development sign-in: fails closed on every malformed, tampered or expired token."""

import time

import pytest

from app.auth import AuthError, mint_dev_token, verify_token
from app.config import ConfigError, Settings
from conftest import dev_settings


def test_round_trip_and_tamper():
    s = dev_settings()
    tok = mint_dev_token(s, "synthetic-1")
    assert verify_token(s, tok) == ("public", "synthetic-1")
    payload, sig = tok.split(".")
    for bad in (payload + "." + sig[:-2] + "AA", payload[:-2] + "xx." + sig, "garbage", "", "a.b.c"):
        with pytest.raises(AuthError):
            verify_token(s, bad)
    with pytest.raises(AuthError):
        verify_token(dev_settings(auth_dev_secret="another-secret-" + "y" * 32), tok)


def test_expiry_and_ttl_cap():
    s = dev_settings()
    tok = mint_dev_token(s, "synthetic-2", ttl=10_000, now=1_000_000)
    verify_token(s, tok, now=1_000_000 + 599)
    with pytest.raises(AuthError):
        verify_token(s, tok, now=1_000_000 + 601)


def test_auth_off_refuses_everything():
    with pytest.raises(AuthError):
        mint_dev_token(dev_settings(auth_mode="off"), "x")
    tok = mint_dev_token(dev_settings(), "x")
    with pytest.raises(AuthError):
        verify_token(dev_settings(auth_mode="off"), tok)


@pytest.mark.parametrize("over", [
    dict(auth_mode="dev", environment="production"),
    dict(auth_mode="dev", environment="staging"),
    dict(auth_mode="dev", auth_dev_secret="short"),
    dict(auth_mode="oauth-someday"),
])
def test_unsafe_configs_refused(over):
    with pytest.raises(ConfigError):
        dev_settings(**over).check()


def test_api_401s(client):
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer nope"}).status_code == 401
    expired = mint_dev_token(dev_settings(), "synthetic-3", now=time.time() - 3600)
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_unknown_tenant_is_401(client):
    tok = client.post("/api/v1/dev/token", json={"subject": "s", "tenant": "no-such-tenant"}).json()["access_token"]
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 401


def test_subject_comes_from_token_not_body(make_user):
    u = make_user()
    r = u.post("/api/v1/consents", json={"purpose": "plan_storage", "user_id": "someone-else"})
    assert r.status_code == 422
