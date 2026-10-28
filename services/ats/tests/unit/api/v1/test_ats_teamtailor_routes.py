import json
import uuid

import pytest
from cryptography.fernet import Fernet
from prepza_common.auth.auth import current_user
from prepza_common.auth.encryption import decrypt
from prepza_common.auth.user import User

from ats.config import settings
from ats.integrations import teamtailor
from ats.integrations.errors import KeyRejected
from ats.main import app
from ats.models.ats import AtsConnection
from ats.repositories import ats, ats_links
from tests.unit.helpers.test_teamtailor_signatures import signature

COMPANY_ID = uuid.uuid4()
HOST = "https://api.na.teamtailor.com"


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
    and Teamtailor accepting only the key "good", in its North American region."""
    key = Fernet.generate_key().decode()
    companies_api["roles"] = {(COMPANY_ID, "ann"): "admin"}
    rows = {"key": key, "connection": None, "members": []}

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

    async def link_for_job(connection_id, job_id):
        return None

    async def region(given):
        if given != "good":
            raise KeyRejected

        return HOST, "Acme"

    async def check(host, given):
        assert (host, given) == (HOST, "good")

    async def member_id(host, given, email):
        rows["members"].append(email)

        return "5"

    monkeypatch.setattr(settings, "ats_encryption_key", key)
    monkeypatch.setattr(ats, "connect", connect)
    monkeypatch.setattr(ats, "connection", connection)
    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)
    monkeypatch.setattr(ats, "set_credentials", set_credentials)
    monkeypatch.setattr(ats_links, "link_for_job", link_for_job)
    monkeypatch.setattr(teamtailor, "region", region)
    monkeypatch.setattr(teamtailor, "check", check)
    monkeypatch.setattr(teamtailor, "member_id", member_id)

    return rows


def connect(client, key="good"):
    return client.put(f"/teamtailor?company_id={COMPANY_ID}", json={"key": key})


def save_key(client, secret):
    return client.put(f"/teamtailor/webhook?company_id={COMPANY_ID}", json={"secret": secret})


def webhook(client, provider="teamtailor"):
    return client.get(f"/{provider}/webhook?company_id={COMPANY_ID}")


def saved(rows) -> dict:
    return json.loads(decrypt(rows["key"], rows["connection"].credentials))


def test_teamtailor_connects_with_its_region_company_name_and_member(client, stored):
    assert connect(client, key=" good ").status_code == 204

    assert saved(stored) == {"host": HOST, "key": "good"}
    assert stored["connection"].account == "Acme"
    assert stored["connection"].member_id == "5"
    assert stored["members"] == ["ann@example.com"]


def test_a_refused_key_isnt_saved(client, stored):
    response = connect(client, key="bad")

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Teamtailor didn't accept this key: it needs Admin and Read/Write"
    )
    assert stored["connection"] is None


def test_the_web_hook_has_no_secret_key_until_one_is_saved_and_a_reconnect_keeps_it(client, stored):
    connect(client)
    connection_id = stored["connection"].id
    before = webhook(client).json()

    assert before["url"].endswith(f"/api/ats/webhooks/teamtailor/{connection_id}")
    assert before["secret"] == ""

    assert save_key(client, " signature-key ").status_code == 204
    assert saved(stored) == {"host": HOST, "key": "good", "webhook_secret": "signature-key"}
    assert webhook(client).json()["secret"] == "signature-key"

    connect(client)

    assert saved(stored)["webhook_secret"] == "signature-key"
    assert stored["connection"].id == connection_id


def test_saving_a_signature_key_needs_a_connection(client, stored):
    assert save_key(client, "signature-key").status_code == 404


def test_only_greenhouse_and_teamtailor_have_a_web_hook_to_set_up(client, stored):
    response = webhook(client, "workable")

    assert response.status_code == 404
    assert response.json()["detail"] == "No web hook to set up"
    # Greenhouse's, while it isn't connected.
    assert webhook(client, "greenhouse").json()["detail"] == "Not connected"


def test_the_web_hook_answers_only_what_the_signature_key_signed(client, stored):
    connect(client)
    url = f"/webhooks/teamtailor/{stored['connection'].id}"
    body = b'{"event_name": "candidate.update", "data": {"id": 1}}'

    # Nothing counts before the signature key is saved.
    assert client.post(url, content=body).status_code == 401

    save_key(client, "signature-key")
    signed = {"TT-Signature": signature("signature-key", body)}
    forged = {"TT-Signature": signature("other", body)}

    assert client.post(url, content=body, headers=signed).status_code == 200
    assert client.post(url, content=body, headers=forged).status_code == 401
    assert client.post(url, content=body).status_code == 401
    # An address no connection has is answered, so Teamtailor doesn't keep sending.
    assert client.post(f"/webhooks/teamtailor/{uuid.uuid4()}", content=body).status_code == 200


def test_a_reconnect_after_the_encryption_key_changed_works_without_the_old_signature_key(
    client, stored
):
    connect(client)
    save_key(client, "signature-key")
    # Sealed with an encryption key that's gone.
    stored["connection"].credentials = Fernet(Fernet.generate_key()).encrypt(b"{}").decode()

    assert connect(client).status_code == 204
    assert saved(stored) == {"host": HOST, "key": "good"}
