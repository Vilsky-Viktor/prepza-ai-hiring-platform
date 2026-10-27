import asyncio
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fake_redis import FakeRedis
from prepza_common.auth.auth import current_user
from prepza_common.auth.encryption import encrypt
from prepza_common.auth.user import User

from app.config.settings import settings
from app.helpers.slack import signed_state, token_hash
from app.integrations import companies
from app.integrations import slack as slack_api
from app.main import app
from app.services import slack as service
from app.storage import slack as storage

KEY = "Zm9vYmFyYmF6cXV4cXV1eGNvcmdlZ3JhdWx0Z2FycGw="
C1 = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    """Slack set up on the server, and Ann signed in as an owner of C1."""
    monkeypatch.setattr(settings, "slack_client_id", "client")
    monkeypatch.setattr(settings, "slack_client_secret", "secret")
    monkeypatch.setattr(settings, "slack_encryption_key", KEY)
    app.dependency_overrides[current_user] = lambda: User(
        uid="u1", email="u1@example.com", email_verified=True, name="Ann"
    )
    member(monkeypatch, editor=True)
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def nonces(monkeypatch):
    """The trips' nonces Redis holds, and how long each lives."""
    fake = FakeRedis()
    monkeypatch.setattr(service, "get_redis", lambda: fake)

    return fake.expiries


def test_a_company_id_that_isnt_one_is_refused_before_companies_is_asked(client, monkeypatch):
    asked = []

    async def access(company_id, user_id):
        asked.append(company_id)

        return {"member": True, "editor": True}

    monkeypatch.setattr(companies, "access", access)

    assert client.get("/slack?company_id=../users/u1").status_code == 422
    assert asked == []


def member(monkeypatch, editor: bool, is_member: bool = True):
    async def access(company_id, user_id):
        return {"member": is_member, "editor": editor}

    monkeypatch.setattr(companies, "access", access)


def test_add_to_slack_goes_to_slacks_page_with_a_signed_state(client, monkeypatch, nonces):
    url = client.get(f"/slack/start?company_id={C1}").json()["url"]
    query = parse_qs(urlparse(url).query)

    assert url.startswith("https://slack.com/oauth/v2/authorize?")
    assert query["scope"] == ["incoming-webhook"]
    assert query["redirect_uri"] == ["http://localhost:8090/api/notifications/slack/callback"]
    assert list(nonces.values()) == [15 * 60]


def test_a_state_works_once_and_only_for_a_current_editor(client, monkeypatch, saved):
    async def exchange(code):
        return {"team": "Acme", "channel": "#hiring", "url": "https://hooks/x", "token": "t"}

    monkeypatch.setattr(slack_api, "exchange", exchange)
    url = client.get(f"/slack/start?company_id={C1}").json()["url"]
    started = parse_qs(urlparse(url).query)["state"][0]

    assert callback(client, f"code=ok&state={started}").status_code == 303
    assert callback(client, f"code=ok&state={started}").status_code == 422

    saved["saved"] = None
    member(monkeypatch, editor=False)

    assert callback(client, f"code=ok&state={state()}").status_code == 403
    assert saved["saved"] is None


def test_a_viewer_cant_add_slack_and_a_stranger_doesnt_see_the_company(client, monkeypatch):
    member(monkeypatch, editor=False)

    assert client.get(f"/slack/start?company_id={C1}").status_code == 403
    assert client.delete(f"/slack?company_id={C1}").status_code == 403

    member(monkeypatch, editor=False, is_member=False)

    assert client.get(f"/slack?company_id={C1}").status_code == 404


def test_slack_not_set_up_on_the_server_says_so(client, monkeypatch):
    monkeypatch.setattr(settings, "slack_client_id", "")
    response = client.get(f"/slack/start?company_id={C1}")

    assert response.status_code == 503
    assert response.json()["detail"] == "Slack isn't set up yet"


def state(expires_in=60):
    """A state whose nonce Redis holds, as if "Add to Slack" was just pressed."""
    nonce = f"n{time.time_ns()}"
    asyncio.run(service.get_redis().set(f"slack:state:{nonce}", 1, ex=1))

    return signed_state(service.state_key(), C1, "u1", int(time.time()) + expires_in, nonce)


@pytest.fixture
def saved(monkeypatch):
    """What the callback saves and which earlier apps it removes; C1 had no channel before, and
    no other company has one."""
    found = {"saved": None, "revoked": [], "earlier": None}

    async def get(company_id):
        return found["earlier"]

    async def connect(*args):
        found["saved"] = args

    async def token_in_use(token_hash):
        return bool(found["saved"]) and found["saved"][5] == token_hash

    async def revoke(token):
        found["revoked"].append(token)

    monkeypatch.setattr(storage, "get", get)
    monkeypatch.setattr(storage, "connect", connect)
    monkeypatch.setattr(storage, "token_in_use", token_in_use)
    monkeypatch.setattr(slack_api, "revoke", revoke)

    return found


def callback(client, query):
    return client.get(f"/slack/callback?{query}", follow_redirects=False)


def test_back_from_slack_the_channel_is_saved_sealed_with_the_default_kinds(
    client, monkeypatch, saved
):
    async def exchange(code):
        return {"team": "Acme", "channel": "#hiring", "url": "https://hooks/x", "token": "t"}

    monkeypatch.setattr(slack_api, "exchange", exchange)
    response = callback(client, f"code=ok&state={state()}")
    company_id, team, channel, webhook, token, hashed, kinds, user_id = saved["saved"]

    assert response.status_code == 303
    assert response.headers["location"].endswith(
        f"/companies/{C1}/integrations/slack?slack=connected"
    )
    assert (company_id, team, channel, user_id) == (C1, "Acme", "#hiring", "u1")
    assert "https://hooks/x" not in webhook and token != "t"
    # The same token always has the same hash, whatever its seal: how other companies on the
    # workspace are found.
    assert hashed == token_hash("t") != token_hash("t2")
    assert "candidate_finished" in kinds and "interview_ready" not in kinds


def test_reconnecting_keeps_the_kinds_and_removes_the_earlier_app(client, monkeypatch, saved):
    async def exchange(code):
        return {"team": "Acme", "channel": "#new", "url": "https://hooks/y", "token": "t2"}

    saved["earlier"] = SimpleNamespace(kinds=["interview_ready"], token=encrypt(KEY, "t1"))
    monkeypatch.setattr(slack_api, "exchange", exchange)
    callback(client, f"code=ok&state={state()}")

    assert saved["saved"][6] == ["interview_ready"]
    assert saved["revoked"] == ["t1"]


def test_reconnecting_to_the_same_workspace_keeps_its_app(client, monkeypatch, saved):
    """Slack gives the same token again: revoking it would remove the app just added."""

    async def exchange(code):
        return {"team": "Acme", "channel": "#new", "url": "https://hooks/y", "token": "t1"}

    saved["earlier"] = SimpleNamespace(kinds=["interview_ready"], token=encrypt(KEY, "t1"))
    monkeypatch.setattr(slack_api, "exchange", exchange)

    assert callback(client, f"code=ok&state={state()}").status_code == 303
    assert saved["revoked"] == []


def test_cancelled_refused_and_expired_trips(client, monkeypatch, saved):
    async def refused(code):
        raise slack_api.SlackRefused("invalid_code")

    monkeypatch.setattr(slack_api, "exchange", refused)

    assert (
        callback(client, f"error=access_denied&state={state()}")
        .headers["location"]
        .endswith("?slack=cancelled")
    )
    assert (
        callback(client, f"code=bad&state={state()}").headers["location"].endswith("?slack=failed")
    )
    assert callback(client, f"code=ok&state={state(-1)}").status_code == 422
    assert saved["saved"] is None


def test_only_known_kinds_are_saved(client, monkeypatch):
    chosen = []

    async def get(company_id):
        return SimpleNamespace()

    async def set_kinds(company_id, kinds, user_id):
        chosen.append((kinds, user_id))

    monkeypatch.setattr(storage, "get", get)
    monkeypatch.setattr(storage, "set_kinds", set_kinds)
    body = {"kinds": ["interview_ready", "made_up", "candidate_finished"]}

    assert client.put(f"/slack/kinds?company_id={C1}", json=body).status_code == 204
    # Saved as the member's change, for the action log.
    assert chosen == [(["candidate_finished", "interview_ready"], "u1")]
