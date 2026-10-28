import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.config.constants import MAX_PAGE_SIZE

from companies.integrations import billing
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, credit_invites

COMPANY_ID = uuid.uuid4()
COMPANY = f"/companies/{COMPANY_ID}"
NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)
INTERVIEW = Interview(
    id=uuid.uuid4(), company_id=COMPANY_ID, generation_id=uuid.uuid4(), title="Backend"
)
INVITE = CandidateInvite(
    id=uuid.uuid4(), interview_id=INTERVIEW.id, email="cid@example.com", name="Cid"
)


def as_member(monkeypatch, role):
    """Bob, signed in, with this role in the company."""
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=NOW, verification_status="none")
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role=role,
            created_at=NOW,
        )
    ]

    async def fake_company(session, _company_id):
        return company

    monkeypatch.setattr(companies, "get", fake_company)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def movement(reason, amount, hold_key=None, transaction_id=None, total=None, note=None):
    return {
        "id": str(uuid.uuid4()),
        "amount": amount,
        "reason": reason,
        "created_at": NOW.isoformat(),
        "total": total,
        "currency": "USD" if total else None,
        "automatic": False,
        "transaction_id": transaction_id,
        "hold_key": hold_key,
        "note": note,
    }


@pytest.mark.parametrize("path", ["history", "reserved"])
def test_a_viewer_doesnt_see_the_billing(client, monkeypatch, path):
    as_member(monkeypatch, "viewer")

    assert client.get(f"{COMPANY}/billing/{path}").status_code == 403


def test_the_history_names_each_candidate_and_only_a_top_up_has_an_invoice(client, monkeypatch):
    as_member(monkeypatch, "admin")
    asked = []

    async def history(company_id, offset, limit):
        asked.append((company_id, offset, limit))

        return [
            movement("candidate", -300, hold_key="hold-cid"),
            movement("candidate", -300, hold_key="hold-gone"),
            movement("refund", -1_000, transaction_id="txn_01", total="1000"),
            movement("topup", 1_000, transaction_id="txn_01", total="1000"),
            movement("welcome", 900),
        ]

    async def by_hold_keys(session, company_id, keys):
        asked.append(keys)

        return {"hold-cid": (INVITE, INTERVIEW)}

    monkeypatch.setattr(billing, "company_history", history)
    monkeypatch.setattr(credit_invites, "by_hold_keys", by_hold_keys)

    response = client.get(f"{COMPANY}/billing/history", params={"offset": 5, "limit": 5})
    cid, gone, refund, topup, welcome = response.json()

    assert asked == [(COMPANY_ID, 5, 5), ["hold-cid", "hold-gone"]]
    assert cid["candidate"] == {
        "invite_id": str(INVITE.id),
        "interview_id": str(INTERVIEW.id),
        "email": "cid@example.com",
        "name": "Cid",
        "interview_title": "Backend",
    }
    assert (cid["candidate_deleted"], gone["candidate"], gone["candidate_deleted"]) == (
        False,
        None,
        True,
    )
    assert [row["invoice_id"] for row in (cid, gone, refund, topup, welcome)] == [
        None,
        None,
        None,
        "txn_01",
        None,
    ]
    assert (topup["total"], topup["currency"]) == ("1000", "USD")
    assert (refund["candidate_deleted"], welcome["candidate_deleted"]) == (False, False)


def test_a_superadmins_adjustment_shows_its_note(client, monkeypatch):
    as_member(monkeypatch, "owner")

    async def history(company_id, offset, limit):
        return [movement("adjustment", 500, note="Complaint 12"), movement("welcome", 900)]

    monkeypatch.setattr(billing, "company_history", history)

    adjustment, welcome = client.get(f"{COMPANY}/billing/history").json()

    assert (adjustment["reason"], adjustment["amount"], adjustment["note"]) == (
        "adjustment",
        500,
        "Complaint 12",
    )
    assert welcome["note"] is None


def test_the_reserved_list_names_the_candidates_holding_credits(client, monkeypatch):
    as_member(monkeypatch, "owner")
    asked = []

    async def holding(session, company_id, offset, limit):
        asked.append((company_id, offset, limit))

        return [(INVITE, INTERVIEW)]

    monkeypatch.setattr(credit_invites, "holding", holding)

    response = client.get(f"{COMPANY}/billing/reserved")

    assert asked == [(COMPANY_ID, 0, MAX_PAGE_SIZE)]
    assert [(row["email"], row["interview_title"]) for row in response.json()] == [
        ("cid@example.com", "Backend")
    ]


def test_the_credits_say_how_many_candidates_hold_the_reserved_ones(client, monkeypatch):
    as_member(monkeypatch, "viewer")

    async def credits(company_id):
        return {"available": 300, "reserved": 600, "low": False, "candidates": 1}

    async def count_holding(session, company_id):
        return 2

    monkeypatch.setattr(billing, "company_credits", credits)
    monkeypatch.setattr(credit_invites, "count_holding", count_holding)

    response = client.get(f"{COMPANY}/credits")

    assert (response.json()["reserved"], response.json()["reserved_candidates"]) == (600, 2)
