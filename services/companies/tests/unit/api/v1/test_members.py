import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user, optional_user
from prepza_common.auth.user import User

from companies.main import app
from companies.models.companies import Company, Member
from companies.repositories import members
from companies.services import outbox as outbox_service

MEMBER_ID = uuid.uuid4()
COMPANY_ID = uuid.uuid4()


def sign_in(email, verified=True, uid="admin"):
    user = User(uid=uid, email=email, email_verified=verified, name="Bob")
    # The invite's page is open to visitors too.
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[optional_user] = lambda: user


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def stored_invite(monkeypatch):
    member = Member(
        id=MEMBER_ID,
        company_id=COMPANY_ID,
        invited_email="bob@example.com",
        token="token-1",
        role="admin",
        created_at=datetime.now(UTC),
    )
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    accepted = []

    async def fake_get(token):
        return (member, company) if token == "token-1" else None

    async def fake_accept(item, company, user_id):
        accepted.append(user_id)

        return True

    monkeypatch.setattr(members, "get_by_token", fake_get)
    monkeypatch.setattr(members, "accept", fake_accept)
    monkeypatch.setattr(outbox_service, "flush_quietly", fake_flush)

    return accepted


def test_invited_email_accepts(client, stored_invite):
    flushed.clear()
    sign_in("Bob@Example.com", uid="bob")

    assert client.post("/members/invites/token-1/accept").status_code == 204
    assert stored_invite == ["bob"]
    # The owner's notification is sent right away, not on the outbox's next run.
    assert flushed


@pytest.mark.parametrize(
    ("email", "verified"), [("eve@example.com", True), ("bob@example.com", False)]
)
def test_other_or_unverified_email_is_rejected(client, stored_invite, email, verified):
    sign_in(email, verified)

    assert client.post("/members/invites/token-1/accept").status_code == 403
    assert stored_invite == []


def test_unknown_token(client, stored_invite):
    sign_in("bob@example.com")

    assert client.post("/members/invites/missing/accept").status_code == 404


def test_a_visitor_sees_the_invite_without_its_email(client, stored_invite):
    response = client.get("/members/invites/token-1")

    assert response.status_code == 200
    assert response.json() == {
        "company_name": "Arcolabs",
        "email": None,
        "matches": False,
        "joined": False,
        "company_id": None,
    }


@pytest.mark.parametrize(
    ("email", "verified", "matches", "shown"),
    [
        ("bob@example.com", True, True, "bob@example.com"),
        ("bob@example.com", False, True, None),
        ("eve@example.com", True, False, None),
    ],
)
def test_only_the_verified_account_invited_sees_the_invites_address(
    client, stored_invite, email, verified, matches, shown
):
    from prepza_common.auth.auth import optional_user

    app.dependency_overrides[optional_user] = lambda: User(
        uid="u1", email=email, email_verified=verified
    )

    found = client.get("/members/invites/token-1").json()

    assert (found["matches"], found["email"]) == (matches, shown)


def test_a_used_link_opens_the_company_for_its_member_and_says_used_to_others(client, monkeypatch):
    member = Member(
        id=MEMBER_ID,
        company_id=COMPANY_ID,
        invited_email="bob@example.com",
        token="token-1",
        role="admin",
        user_id="bob",
        created_at=datetime.now(UTC),
    )
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))

    async def fake_get(token):
        return member, company

    monkeypatch.setattr(members, "get_by_token", fake_get)
    sign_in("bob@example.com", uid="bob")
    mine = client.get("/members/invites/token-1").json()
    sign_in("eve@example.com", uid="eve")
    theirs = client.get("/members/invites/token-1").json()

    assert (mine["joined"], mine["company_id"]) == (True, str(COMPANY_ID))
    assert (theirs["joined"], theirs["company_id"]) == (True, None)


def test_invite_view(client, stored_invite):
    sign_in("bob@example.com")
    response = client.get("/members/invites/token-1")

    assert response.status_code == 200
    assert response.json() == {
        "company_name": "Arcolabs",
        "email": "bob@example.com",
        "matches": True,
        "joined": False,
        "company_id": None,
    }


# How many times the outbox was asked to send its events right away.
flushed = []


async def fake_flush():
    flushed.append(True)
