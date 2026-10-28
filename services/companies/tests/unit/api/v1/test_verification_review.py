import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.helpers.notifications import verification_decided
from companies.main import app
from companies.models.companies import Company, Member
from companies.repositories import companies, verification
from companies.services import outbox as outbox_service

COMPANY_ID = uuid.uuid4()
URL = f"/superadmin/verifications/{COMPANY_ID}"
# What the superadmin saw in the list.
SEEN = {"name": "Acme", "domain": "acme.com"}


def pending_company():
    company = Company(
        id=COMPANY_ID,
        name="Acme",
        website_domain="acme.com",
        verification_status="pending",
        verification_name="Acme",
        verification_email="ann@acme.com",
        verification_submitted_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    company.members = [
        Member(company_id=COMPANY_ID, user_id="ann", invited_email="ann@acme.com", role="owner"),
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="b@x.com", role="admin"),
        Member(company_id=COMPANY_ID, user_id="vic", invited_email="v@x.com", role="viewer"),
        Member(company_id=COMPANY_ID, user_id=None, invited_email="new@x.com", role="admin"),
    ]

    return company


@pytest.fixture
def superadmin(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "root@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="root",
        email="root@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def decisions(monkeypatch):
    """The pending company, and the decisions storage got: (approved, uid, reason, notices)."""
    company = pending_company()
    made = []

    async def fake_get(_id):
        return company if _id == COMPANY_ID else None

    async def fake_decide(_id, approved, superadmin_id, reason, notices, seen=None):
        if company.verification_status != "pending":
            return False

        if seen is not None and seen != (company.verification_name, company.website_domain):
            return False

        company.verification_status = "approved" if approved else "declined"
        made.append((approved, superadmin_id, reason, notices))

        return True

    async def no_flush():
        return None

    monkeypatch.setattr(companies, "get", fake_get)
    monkeypatch.setattr(verification, "decide", fake_decide)
    monkeypatch.setattr(outbox_service, "flush_quietly", no_flush)

    return made


def test_approving_tells_the_owners_and_admins(client, superadmin, decisions):
    assert client.post(f"{URL}/approve", json=SEEN).status_code == 204

    [(approved, uid, reason, notices)] = decisions

    assert (approved, uid, reason) == (True, "root", None)
    assert [notice["recipient_id"] for notice in notices] == ["ann", "bob"]
    assert notices[0]["kind"] == "verification_approved"
    assert notices[0]["data"] == {"name": "Acme", "domain": "acme.com"}
    assert notices[0]["link"] == f"/companies/{COMPANY_ID}/interviews"


def test_declining_keeps_the_reason_and_says_it(client, superadmin, decisions):
    response = client.post(f"{URL}/decline", json={"reason": "  Not the same company "})

    assert response.status_code == 204

    [(approved, _, reason, notices)] = decisions

    assert (approved, reason) == (False, "Not the same company")
    assert notices[0]["kind"] == "verification_declined"
    assert notices[0]["data"]["reason"] == "Not the same company"


def test_a_decline_without_a_reason_says_none(client, superadmin, decisions):
    client.post(f"{URL}/decline", json={})

    assert decisions[0][2] is None
    assert "reason" not in decisions[0][3][0]["data"]


def test_a_decided_request_cant_be_decided_again(client, superadmin, decisions):
    assert client.post(f"{URL}/approve", json=SEEN).status_code == 204
    assert client.post(f"{URL}/decline", json={}).status_code == 409
    assert (
        client.post(f"/superadmin/verifications/{uuid.uuid4()}/approve", json=SEEN).status_code
        == 404
    )


def test_the_list_shows_what_to_review(client, superadmin, monkeypatch):
    asked = []

    async def fake_requests(offset, limit):
        asked.append((offset, limit))

        return [pending_company()]

    monkeypatch.setattr(verification, "requests", fake_requests)

    [row] = client.get("/superadmin/verifications?offset=20&limit=10").json()

    assert asked == [(20, 10)]
    assert (row["name"], row["domain"], row["email"], row["status"]) == (
        "Acme",
        "acme.com",
        "ann@acme.com",
        "pending",
    )


def test_review_is_only_for_superadmins(client, decisions):
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@acme.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    assert client.get("/superadmin/verifications").status_code == 404
    assert client.post(f"{URL}/approve", json=SEEN).status_code == 404
    assert client.post(f"{URL}/decline", json={}).status_code == 404
    assert decisions == []

    app.dependency_overrides.clear()


def test_notices_fall_back_to_the_company_name():
    company = pending_company()
    company.verification_name = None

    assert verification_decided(company, True, None)[0]["data"]["name"] == "Acme"


def test_a_request_renamed_since_it_was_seen_isnt_approved(client, superadmin, decisions):
    response = client.post(f"{URL}/approve", json={"name": "Old name", "domain": "acme.com"})

    assert response.status_code == 409
    assert response.json()["detail"] == "This request changed; check it again."
    assert decisions == []
