import json
import uuid

import pytest
from cryptography.fernet import Fernet
from prepza_common.auth import current_user
from prepza_common.encryption import decrypt
from prepza_common.user import User

from app.config.settings import settings
from app.integrations import recruitee
from app.integrations.errors import KeyRejected
from app.main import app
from app.models.ats import AtsConnection
from app.storage import ats, ats_links
from tests.unit.test_recruitee import signature

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
    and Recruitee accepting only the token "good" for the company acme."""
    key = Fernet.generate_key().decode()
    companies_api["roles"] = {(COMPANY_ID, "ann"): "admin"}
    rows = {"key": key, "connection": None, "checked": []}

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

    async def check(company, token):
        rows["checked"].append((company, token))

        if (company, token) != ("acme", "good"):
            raise KeyRejected

    monkeypatch.setattr(settings, "ats_encryption_key", key)
    monkeypatch.setattr(ats, "connect", connect)
    monkeypatch.setattr(ats, "connection", connection)
    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)
    monkeypatch.setattr(ats, "set_credentials", set_credentials)
    monkeypatch.setattr(ats_links, "link_for_job", link_for_job)
    monkeypatch.setattr(recruitee, "check", check)

    return rows


def connect(client, account="acme.recruitee.com", token="good"):
    return client.put(
        f"/recruitee?company_id={COMPANY_ID}", json={"account": account, "token": token}
    )


def save_key(client, secret, provider="recruitee"):
    return client.put(f"/{provider}/webhook?company_id={COMPANY_ID}", json={"secret": secret})


def webhook(client):
    return client.get(f"/recruitee/webhook?company_id={COMPANY_ID}")


def saved(rows) -> dict:
    return json.loads(decrypt(rows["key"], rows["connection"].credentials))


def test_recruitee_connects_with_the_companys_subdomain_and_token(client, stored):
    assert (
        connect(client, account=" https://Acme.recruitee.com/ ", token=" good ").status_code == 204
    )

    assert stored["checked"] == [("acme", "good")]
    assert saved(stored) == {"company": "acme", "token": "good"}
    assert stored["connection"].account == "acme"
    assert stored["connection"].member_id is None


def test_an_address_that_isnt_one_isnt_checked(client, stored):
    response = connect(client, account="not an address")

    assert response.status_code == 422
    assert response.json()["detail"] == "Enter your Recruitee address, like acme.recruitee.com"
    assert stored["checked"] == [] and stored["connection"] is None


def test_a_refused_token_isnt_saved(client, stored):
    response = connect(client, token="bad")

    assert response.status_code == 422
    assert response.json()["detail"] == "Recruitee didn't accept this token for that company"
    assert stored["connection"] is None


def test_the_web_hook_has_no_secret_until_one_is_saved_and_a_reconnect_keeps_it(client, stored):
    connect(client)
    connection_id = stored["connection"].id
    before = webhook(client).json()

    assert before["url"].endswith(f"/api/ats/webhooks/recruitee/{connection_id}")
    assert before["secret"] == ""

    assert save_key(client, " web-hook-secret ").status_code == 204
    assert saved(stored) == {
        "company": "acme",
        "token": "good",
        "webhook_secret": "web-hook-secret",
    }
    assert webhook(client).json()["secret"] == "web-hook-secret"

    connect(client)

    assert saved(stored)["webhook_secret"] == "web-hook-secret"
    assert stored["connection"].id == connection_id


def test_saving_a_secret_needs_a_connection(client, stored):
    assert save_key(client, "web-hook-secret").status_code == 404


@pytest.mark.parametrize("provider", ["workable", "greenhouse"])
def test_only_atss_that_make_the_secret_have_one_to_save(client, stored, provider):
    response = save_key(client, "web-hook-secret", provider)

    assert response.status_code == 404
    assert response.json()["detail"] == "No web hook key to save"


def test_the_web_hook_answers_only_what_the_secret_signed(client, stored):
    connect(client)
    url = f"/webhooks/recruitee/{stored['connection'].id}"
    body = b'{"event_type": "candidate_moved", "event_subtype": "stage_changed", "payload": {}}'

    # Before the secret is saved (Recruitee's test among them), events are answered and ignored.
    assert client.post(url, content=body).status_code == 200

    save_key(client, "web-hook-secret")
    signed = {"X-Recruitee-Signature": signature("web-hook-secret", body)}
    forged = {"X-Recruitee-Signature": signature("other", body)}

    assert client.post(url, content=body, headers=signed).status_code == 200
    assert client.post(url, content=body, headers=forged).status_code == 401
    assert client.post(url, content=body).status_code == 401
    # An address no connection has is answered, so Recruitee doesn't keep sending.
    assert client.post(f"/webhooks/recruitee/{uuid.uuid4()}", content=body).status_code == 200
