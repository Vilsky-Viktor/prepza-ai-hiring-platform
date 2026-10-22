import hashlib
import hmac
import json
import uuid

import pytest
from cryptography.fernet import Fernet
from prepza_common.auth import current_user
from prepza_common.encryption import decrypt
from prepza_common.user import User

from app.config.settings import settings
from app.integrations import greenhouse
from app.integrations.errors import KeyRejected
from app.main import app
from app.models.ats import AtsConnection
from app.storage import ats, ats_links

COMPANY_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def signed_in_admin():
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True
    )
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def stored(monkeypatch, companies_api):
    """A company Ann administers, its Greenhouse connection kept in memory (encrypted with a
    fresh key), and Greenhouse accepting only the secret "good"."""
    key = Fernet.generate_key().decode()
    companies_api["roles"] = {(COMPANY_ID, "ann"): "admin"}
    rows = {"key": key, "connection": None, "can_write": True}

    async def connect(
        company_id, provider, account, credentials, user_id, member_id=None, language=None
    ):
        earlier = rows["connection"]
        rows["connection"] = AtsConnection(
            id=earlier.id if earlier else uuid.uuid4(),
            company_id=company_id,
            provider=provider,
            account=account,
            credentials=credentials,
            member_id=member_id,
            status="connected",
            created_by=user_id,
        )

    async def connection(company_id, provider):
        return rows["connection"]

    async def connection_by_id(connection_id):
        found = rows["connection"]

        return found if found and found.id == connection_id else None

    async def link_for_job(connection_id, job_id):
        return None

    async def check(client_id, client_secret):
        if client_secret != "good":
            raise KeyRejected

    monkeypatch.setattr(settings, "ats_encryption_key", key)
    monkeypatch.setattr(ats, "connect", connect)
    monkeypatch.setattr(ats, "connection", connection)
    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)
    monkeypatch.setattr(ats_links, "link_for_job", link_for_job)

    async def can_write(client_id, client_secret):
        return rows["can_write"]

    monkeypatch.setattr(greenhouse, "check", check)
    monkeypatch.setattr(greenhouse, "can_write", can_write)

    return rows


def connect(client, client_id="client-1234", secret="good"):
    return client.put(
        f"/greenhouse?company_id={COMPANY_ID}",
        json={"client_id": client_id, "client_secret": secret},
    )


def saved(rows) -> dict:
    return json.loads(decrypt(rows["key"], rows["connection"].credentials))


def test_greenhouse_connects_with_a_secret_key_for_its_web_hook(client, stored):
    assert connect(client, client_id=" client-1234 ").status_code == 204

    found = saved(stored)
    # Greenhouse names no account: the page shows the company's name instead.
    assert stored["connection"].account == ""
    assert stored["connection"].member_id is None
    assert (found["client_id"], found["client_secret"]) == ("client-1234", "good")
    assert len(found["webhook_secret"]) >= 32

    webhook = client.get(f"/greenhouse/webhook?company_id={COMPANY_ID}").json()
    connection_id = stored["connection"].id
    assert webhook["url"].endswith(f"/api/ats/webhooks/greenhouse/{connection_id}")
    assert webhook["secret"] == found["webhook_secret"]


def test_a_reconnect_keeps_the_web_hooks_secret_key(client, stored):
    connect(client)
    first = saved(stored)["webhook_secret"]
    connect(client, client_id="client-5678")

    assert saved(stored)["webhook_secret"] == first


def test_a_refused_credential_isnt_saved(client, stored):
    response = connect(client, secret="bad")

    assert response.status_code == 422
    assert stored["connection"] is None
    assert client.get(f"/greenhouse/webhook?company_id={COMPANY_ID}").status_code == 404


def test_a_credential_that_cant_add_notes_isnt_saved(client, stored):
    """Results couldn't go back: Greenhouse lists its scopes without the one notes need."""
    stored["can_write"] = False
    response = connect(client)

    assert response.status_code == 422
    assert "can't add notes" in response.json()["detail"]
    assert stored["connection"] is None


def test_the_web_hook_answers_only_what_its_secret_key_signed(client, stored):
    connect(client)
    secret = saved(stored)["webhook_secret"]
    url = f"/webhooks/greenhouse/{stored['connection'].id}"
    body = b'{"action": "ping"}'
    signature = "sha256 " + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert client.post(url, content=body, headers={"Signature": signature}).status_code == 200
    assert client.post(url, content=body, headers={"Signature": "sha256 x"}).status_code == 401
    assert client.post(url, content=body).status_code == 401
    # An address no connection has is answered, so Greenhouse doesn't keep sending.
    other = f"/webhooks/greenhouse/{uuid.uuid4()}"
    assert client.post(other, content=body).status_code == 200
