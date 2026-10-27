import logging
from types import SimpleNamespace

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from app.helpers.unsubscribe import address_hash
from app.integrations import companies
from app.main import app
from app.storage import opt_outs

ANN = address_hash("ann@example.com")
URL = "/superadmin/candidate-opt-outs"
# Companies' ids, in this order when sorted.
ACME, BOLT, COLD, ZETA = (f"00000000-0000-0000-0000-00000000000{end}" for end in "abcf")


@pytest.fixture
def signed_in(monkeypatch):
    """Acme and Bolt invited Ann; Ann stopped Acme's emails and one of Bolt's invites' reminders,
    and a superadmin stopped Cold's emails before Cold erased her. Signs in as the superadmin
    Sam, or as `email`."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    rows = [
        SimpleNamespace(company_id=ACME, invite_id=None, by_admin=False),
        SimpleNamespace(company_id=BOLT, invite_id="i-1", by_admin=False),
        SimpleNamespace(company_id=COLD, invite_id=None, by_admin=True),
    ]
    calls = SimpleNamespace(added=[], removed=[], invited=[], names=[])

    async def of_address(address):
        return rows if address == ANN else []

    async def add(address, company_id, invite_id=None, by_admin=False):
        calls.added.append((address, company_id, invite_id, by_admin))

    async def remove_admin_stop(address, company_id):
        calls.removed.append((address, company_id))

    async def invited_company_ids(email):
        calls.invited.append(email)

        return [BOLT, ACME]

    async def members(company_ids):
        calls.names.append(company_ids)
        names = {ACME: "acme", BOLT: "Bolt", COLD: "Cold"}

        return [{"id": id, "name": names[id], "members": []} for id in company_ids]

    monkeypatch.setattr(opt_outs, "of_address", of_address)
    monkeypatch.setattr(opt_outs, "add", add)
    monkeypatch.setattr(opt_outs, "remove_admin_stop", remove_admin_stop)
    monkeypatch.setattr(companies, "invited_company_ids", invited_company_ids)
    monkeypatch.setattr(companies, "members", members)

    def sign_in(email="sam@prepza.dev"):
        app.dependency_overrides[current_user] = lambda: User(
            uid="sam",
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    sign_in()
    calls.sign_in = sign_in
    yield calls

    app.dependency_overrides.clear()


def test_the_lookup_lists_invited_and_opted_out_companies_by_name_whatever_the_case(
    client, signed_in
):
    response = client.post(f"{URL}/lookup", json={"email": "Ann@Example.com"})

    assert response.status_code == 200
    assert response.json() == {
        "companies": [
            {
                "company_id": ACME,
                "name": "acme",
                "stopped": True,
                "stopped_by_admin": False,
                "stopped_reminders": 0,
            },
            {
                "company_id": BOLT,
                "name": "Bolt",
                "stopped": False,
                "stopped_by_admin": False,
                "stopped_reminders": 1,
            },
            {
                "company_id": COLD,
                "name": "Cold",
                "stopped": True,
                "stopped_by_admin": True,
                "stopped_reminders": 0,
            },
        ]
    }
    # Every name in one call to companies.
    assert signed_in.names == [[ACME, BOLT, COLD]]


def test_a_superadmin_stops_an_inviting_companys_emails_and_it_is_logged(client, signed_in, caplog):
    body = {"email": "ann@example.com", "company_id": BOLT, "stopped": True}

    with caplog.at_level(logging.WARNING):
        response = client.put(URL, json=body)

    assert response.status_code == 200
    assert signed_in.added == [(ANN, BOLT, None, True)]
    assert "by superadmin sam" in caplog.text
    assert "ann@example.com" not in caplog.text


def test_only_a_company_that_invited_the_address_can_be_stopped(client, signed_in):
    body = {"email": "ann@example.com", "company_id": ZETA, "stopped": True}

    assert client.put(URL, json=body).status_code == 404
    assert signed_in.added == []


def test_a_superadmin_lifts_a_superadmins_stop(client, signed_in):
    body = {"email": "ANN@example.com", "company_id": COLD, "stopped": False}

    assert client.put(URL, json=body).status_code == 200
    assert signed_in.removed == [(ANN, COLD)]


def test_anyone_else_gets_not_found(client, signed_in):
    signed_in.sign_in("bob@example.com")
    body = {"email": "ann@example.com", "company_id": BOLT, "stopped": True}

    lookup = client.post(f"{URL}/lookup", json={"email": "ann@example.com"})
    change = client.put(URL, json=body)

    assert (lookup.status_code, change.status_code) == (404, 404)
    assert (signed_in.invited, signed_in.added) == ([], [])


def test_signed_out_gets_401(client):
    # Signed out, as everyone else: the admin zone isn't there.
    assert client.post(f"{URL}/lookup", json={"email": "a@b.c"}).status_code == 404
