import json
import uuid

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.encryption import decrypt
from prepza_common.auth.user import User

from app.config.settings import settings
from app.integrations import breezy
from app.integrations.errors import KeyRejected
from app.main import app
from app.models.ats import AtsConnection
from app.storage import ats, ats_links
from tests.unit.test_breezy import signature

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
    """A company Ann administers, its connections kept in memory (encrypted with a fresh key),
    and Breezy HR knowing the key "good" (company c1, Acme), creating web hooks w1, w2... and
    recording the ones deleted."""
    key = Fernet.generate_key().decode()
    companies_api["roles"] = {(COMPANY_ID, "ann"): "admin"}
    rows = {"key": key, "connection": None, "hooks": [], "deleted": []}
    companies = {"good": {"id": "c1", "name": "Acme"}, "nobody": None}

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
        found = rows["connection"]

        return found if found and found.provider == provider else None

    async def connection_by_id(connection_id):
        found = rows["connection"]

        return found if found and found.id == connection_id else None

    async def set_credentials(connection_id, credentials):
        assert connection_id == rows["connection"].id
        rows["connection"].credentials = credentials

    async def disconnect(company_id, provider, user_id=None):
        rows["connection"] = None
        # Who disconnected it, for the action log (None when prepza undid its own connect).
        rows.setdefault("disconnected_by", []).append(user_id)

    async def restore_broken(earlier):
        rows["connection"] = earlier
        earlier.status = "broken"

    async def link_for_job(connection_id, job_id):
        return None

    async def subscriptions(company_id, link_id=None):
        return []

    async def company(token):
        if token not in companies:
            raise KeyRejected

        return companies[token]

    async def check(company, token):
        return None

    async def subscribe(company, token, url):
        rows["hooks"].append(url)

        return f"w{len(rows['hooks'])}", f"secret-{len(rows['hooks'])}"

    async def unsubscribe(company, token, endpoint_id):
        rows["deleted"].append(endpoint_id)

    for name, fake in {
        "connect": connect,
        "connection": connection,
        "connection_by_id": connection_by_id,
        "set_credentials": set_credentials,
        "disconnect": disconnect,
        "restore_broken": restore_broken,
    }.items():
        monkeypatch.setattr(ats, name, fake)
    monkeypatch.setattr(ats_links, "link_for_job", link_for_job)
    monkeypatch.setattr(ats_links, "subscriptions", subscriptions)
    monkeypatch.setattr(settings, "ats_encryption_key", key)
    monkeypatch.setattr(breezy, "company", company)
    monkeypatch.setattr(breezy, "check", check)
    monkeypatch.setattr(breezy, "subscribe", subscribe)
    monkeypatch.setattr(breezy, "unsubscribe", unsubscribe)

    return rows


def connect(client, token="good"):
    return client.put(f"/breezy?company_id={COMPANY_ID}", json={"token": token})


def saved(rows) -> dict:
    return json.loads(decrypt(rows["key"], rows["connection"].credentials))


def test_breezy_connects_with_a_key_and_creates_its_web_hook(client, stored):
    assert connect(client, token=" good ").status_code == 204

    connection_id = stored["connection"].id
    assert stored["connection"].account == "Acme"
    assert stored["connection"].member_id is None
    assert stored["hooks"][0].endswith(f"/api/ats/webhooks/breezy/{connection_id}")
    assert saved(stored) == {
        "company": "c1",
        "token": "good",
        "webhook_id": "w1",
        "webhook_secret": "secret-1",
    }


def test_a_refused_key_isnt_saved(client, stored):
    response = connect(client, token="bad")

    assert response.status_code == 422
    assert response.json()["detail"] == "Breezy HR didn't accept this key"
    assert stored["connection"] is None and stored["hooks"] == []


def test_a_key_whose_person_has_no_company_isnt_saved(client, stored):
    response = connect(client, token="nobody")

    assert response.status_code == 422
    assert response.json()["detail"] == "This key's person has no Breezy HR company"
    assert stored["connection"] is None and stored["hooks"] == []


@pytest.mark.parametrize("failure", [KeyRejected(), HTTPException(502)])
def test_without_its_web_hook_the_connection_doesnt_stay(client, stored, monkeypatch, failure):
    async def refuse(company, token, url):
        raise failure

    monkeypatch.setattr(breezy, "subscribe", refuse)
    response = connect(client)

    assert response.status_code == 409
    assert "web hooks come with Breezy's Pro plan" in response.json()["detail"]
    assert stored["connection"] is None
    # Disconnected as Ann's, so the company's action log shows it didn't stay.
    assert stored["disconnected_by"] == ["ann"]


def test_a_failed_reconnect_keeps_the_earlier_connection_marked_for_reconnecting(
    client, stored, monkeypatch
):
    connect(client)
    earlier = stored["connection"]

    async def refuse(company, token, url):
        raise HTTPException(502)

    monkeypatch.setattr(breezy, "subscribe", refuse)
    response = connect(client)

    assert response.status_code == 409
    # Not disconnected (which would delete its linked jobs and candidates): its key is back.
    assert stored["connection"].id == earlier.id
    assert stored["connection"].status == "broken"
    assert saved(stored)["webhook_secret"] == "secret-1"


def test_a_reconnect_replaces_the_earlier_web_hook(client, stored):
    connect(client)
    connection_id = stored["connection"].id
    connect(client)

    assert stored["deleted"] == ["w1"]
    assert saved(stored)["webhook_id"] == "w2"
    assert stored["connection"].id == connection_id


def test_disconnecting_deletes_the_web_hook(client, stored):
    connect(client)

    assert client.delete(f"/breezy?company_id={COMPANY_ID}").status_code == 204
    assert stored["deleted"] == ["w1"]
    assert stored["connection"] is None
    assert stored["disconnected_by"] == ["ann"]


def test_the_web_hook_answers_only_what_its_secret_signed(client, stored):
    connect(client)
    url = f"/webhooks/breezy/{stored['connection'].id}"
    body = b'{"type": "candidateStatusUpdated", "object": {}}'
    signed = {"X-Hook-Signature": signature("secret-1", body)}
    forged = {"X-Hook-Signature": signature("other", body)}

    assert client.post(url, content=body, headers=signed).status_code == 200
    assert client.post(url, content=body, headers=forged).status_code == 401
    assert client.post(url, content=body).status_code == 401
    # An address no connection has is answered, so Breezy doesn't keep sending.
    assert client.post(f"/webhooks/breezy/{uuid.uuid4()}", content=body).status_code == 200
