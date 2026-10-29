"""The four key-based ATSs' routes, faked below the route: Ann administers a company whose
connections are kept in memory (encrypted with a fresh key), and each ATS accepts only "good"."""

import json
import uuid

from cryptography.fernet import Fernet
from prepza_common.auth.auth import current_user
from prepza_common.auth.encryption import decrypt
from prepza_common.auth.user import User

from ats.config import settings
from ats.integrations import breezy, greenhouse, recruitee, teamtailor
from ats.integrations.errors import KeyRejected
from ats.main import app
from ats.models.ats import AtsConnection
from ats.repositories import ats, ats_links

COMPANY_ID = uuid.uuid4()
TEAMTAILOR_HOST = "https://api.na.teamtailor.com"
# What each ATS's connect form sends when everything is right.
GOOD = {
    "breezy": {"token": "good"},
    "greenhouse": {"client_id": "client-1234", "client_secret": "good"},
    "recruitee": {"account": "acme.recruitee.com", "token": "good"},
    "teamtailor": {"key": "good"},
}


def store_connections(monkeypatch, companies_api) -> dict:
    """Ann signed in as the company's admin, and its connections kept in `rows`."""
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True
    )
    key = Fernet.generate_key().decode()
    companies_api["roles"] = {(COMPANY_ID, "ann"): "admin"}
    rows = {"key": key, "connection": None}

    async def connect(
        session, company_id, provider, account, credentials, user_id, member_id=None, language=None
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

    async def connection(session, company_id, provider):
        found = rows["connection"]

        return found if found and found.provider == provider else None

    async def connection_by_id(session, connection_id):
        found = rows["connection"]

        return found if found and found.id == connection_id else None

    async def set_credentials(session, connection_id, credentials):
        assert connection_id == rows["connection"].id
        rows["connection"].credentials = credentials

    async def disconnect(session, company_id, provider, user_id=None):
        rows["connection"] = None
        # Who disconnected it, for the action log (None when prepza undid its own connect).
        rows.setdefault("disconnected_by", []).append(user_id)

    async def restore_broken(session, earlier):
        rows["connection"] = earlier
        earlier.status = "broken"

    async def link_for_job(session, connection_id, job_id):
        return None

    async def subscriptions(session, company_id, link_id=None):
        return []

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

    return rows


def fake_breezy(monkeypatch, rows):
    """Breezy HR knowing the key "good" (company c1, Acme), creating web hooks w1, w2... and
    recording the ones deleted."""
    rows.update(hooks=[], deleted=[])
    companies = {"good": {"id": "c1", "name": "Acme"}, "nobody": None}

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

    monkeypatch.setattr(breezy, "company", company)
    monkeypatch.setattr(breezy, "check", check)
    monkeypatch.setattr(breezy, "subscribe", subscribe)
    monkeypatch.setattr(breezy, "unsubscribe", unsubscribe)


def fake_greenhouse(monkeypatch, rows):
    """Greenhouse accepting only the secret "good", whose notes it may add while `can_write`."""
    rows["can_write"] = True

    async def check(client_id, client_secret):
        if client_secret != "good":
            raise KeyRejected

    async def can_write(client_id, client_secret):
        return rows["can_write"]

    monkeypatch.setattr(greenhouse, "check", check)
    monkeypatch.setattr(greenhouse, "can_write", can_write)


def fake_recruitee(monkeypatch, rows):
    """Recruitee accepting only the token "good" for the company acme, recording each check."""
    rows["checked"] = []

    async def check(company, token):
        rows["checked"].append((company, token))

        if (company, token) != ("acme", "good"):
            raise KeyRejected

    monkeypatch.setattr(recruitee, "check", check)


def fake_teamtailor(monkeypatch, rows):
    """Teamtailor accepting only the key "good", in its North American region, recording whose
    member id was looked up."""
    rows["members"] = []

    async def region(given):
        if given != "good":
            raise KeyRejected

        return TEAMTAILOR_HOST, "Acme"

    async def check(host, given):
        assert (host, given) == (TEAMTAILOR_HOST, "good")

    async def member_id(host, given, email):
        rows["members"].append(email)

        return "5"

    monkeypatch.setattr(teamtailor, "region", region)
    monkeypatch.setattr(teamtailor, "check", check)
    monkeypatch.setattr(teamtailor, "member_id", member_id)


FAKES = {
    "breezy": fake_breezy,
    "greenhouse": fake_greenhouse,
    "recruitee": fake_recruitee,
    "teamtailor": fake_teamtailor,
}


def stored_for(provider, monkeypatch, companies_api) -> dict:
    rows = store_connections(monkeypatch, companies_api)
    FAKES[provider](monkeypatch, rows)

    return rows


def connect(client, provider, **body):
    return client.put(f"/{provider}?company_id={COMPANY_ID}", json={**GOOD[provider], **body})


def save_key(client, secret, provider):
    return client.put(f"/{provider}/webhook?company_id={COMPANY_ID}", json={"secret": secret})


def webhook(client, provider):
    return client.get(f"/{provider}/webhook?company_id={COMPANY_ID}")


def saved(rows) -> dict:
    return json.loads(decrypt(rows["key"], rows["connection"].credentials))
