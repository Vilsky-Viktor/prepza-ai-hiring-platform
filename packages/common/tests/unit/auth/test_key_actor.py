import jwt
import pytest
from prepza_common.auth.key_actor import actor_key, key_actor, key_user
from prepza_common.auth.service_auth import issue_token
from prepza_common.config.constants import KEY_SIGN_IN

KEY_ID = "5b0f6a3e-2c1d-4e8f-9a0b-1c2d3e4f5a6b"
SECRET = "companies-own-secret"


@pytest.fixture(autouse=True)
def own_secret(monkeypatch):
    monkeypatch.setenv("SERVICE_SECRET", SECRET)


def test_a_key_acts_as_itself_and_is_told_from_a_person():
    actor = key_actor(KEY_ID)

    assert actor_key(actor) == KEY_ID
    assert actor_key("firebase-uid") is None
    assert actor_key(None) is None


def test_the_assistants_token_for_a_key_signs_in_as_the_key():
    token = issue_token("mcp", "companies", SECRET, {"key": KEY_ID, "company": "c1"})
    user = key_user(token)

    assert (user.uid, user.email, user.sign_in_provider) == (key_actor(KEY_ID), "", KEY_SIGN_IN)


@pytest.mark.parametrize(
    "token",
    [
        # Signed with another service's key.
        issue_token("mcp", "library", "another-secret", {"key": KEY_ID}),
        # Not issued for an AI agent's key.
        issue_token("assistant", "companies", SECRET, {"key": KEY_ID}),
        # No key named.
        issue_token("mcp", "companies", SECRET),
        # Not a token at all.
        "not-a-token",
        # Expired.
        jwt.encode({"iss": "mcp", "aud": "companies", "key": KEY_ID, "exp": 1}, SECRET),
    ],
)
def test_any_other_token_is_no_key(token):
    assert key_user(token) is None


def test_a_service_without_its_own_key_takes_no_key_token(monkeypatch):
    token = issue_token("mcp", "companies", SECRET, {"key": KEY_ID})
    monkeypatch.delenv("SERVICE_SECRET")

    assert key_user(token) is None
