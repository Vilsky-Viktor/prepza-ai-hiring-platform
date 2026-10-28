import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.config.constants import MAX_PAGE_SIZE

from companies.api.v1 import billing as billing_routes
from companies.integrations import billing, billing_prices
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

    async def fake_company(_company_id):
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


@pytest.mark.parametrize("path", ["history", "reserved", "invoice?transaction_id=txn_01"])
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

    async def by_hold_keys(company_id, keys):
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

    async def holding(company_id, offset, limit):
        asked.append((company_id, offset, limit))

        return [(INVITE, INTERVIEW)]

    monkeypatch.setattr(credit_invites, "holding", holding)

    response = client.get(f"{COMPANY}/billing/reserved")

    assert asked == [(COMPANY_ID, 0, MAX_PAGE_SIZE)]
    assert [(row["email"], row["interview_title"]) for row in response.json()] == [
        ("cid@example.com", "Backend")
    ]


def test_an_owner_opens_a_top_ups_invoice_and_billings_404_passes_through(client, monkeypatch):
    as_member(monkeypatch, "owner")

    async def invoice(company_id, transaction_id):
        if transaction_id != "txn_01":
            raise HTTPException(404, "Not found")

        return "https://paddle.test/txn_01.pdf"

    monkeypatch.setattr(billing, "company_invoice", invoice)

    ours = client.get(f"{COMPANY}/billing/invoice", params={"transaction_id": "txn_01"})
    theirs = client.get(f"{COMPANY}/billing/invoice", params={"transaction_id": "txn_99"})

    assert ours.json() == {"url": "https://paddle.test/txn_01.pdf"}
    assert theirs.status_code == 404


def test_the_credits_say_how_many_candidates_hold_the_reserved_ones(client, monkeypatch):
    as_member(monkeypatch, "viewer")

    async def credits(company_id):
        return {"available": 300, "reserved": 600, "low": False, "candidates": 1}

    async def count_holding(company_id):
        return 2

    monkeypatch.setattr(billing, "company_credits", credits)
    monkeypatch.setattr(credit_invites, "count_holding", count_holding)

    response = client.get(f"{COMPANY}/credits")

    assert (response.json()["reserved"], response.json()["reserved_candidates"]) == (600, 2)


def test_an_admin_gets_a_checkout_billing_made_and_a_viewer_none(client, monkeypatch):
    made = []

    async def checkout(company_id, candidates, buyer_id, country, language):
        made.append((company_id, candidates, buyer_id, language))

        return "txn_new"

    monkeypatch.setattr(billing_prices, "company_checkout", checkout)
    as_member(monkeypatch, "admin")
    # The item is named in the interface language the site sends.
    admin = client.post(
        f"{COMPANY}/billing/checkout", json={"candidates": 45}, headers={"Accept-Language": "de-DE"}
    )
    as_member(monkeypatch, "viewer")
    viewer = client.post(f"{COMPANY}/billing/checkout", json={"candidates": 45})
    app.dependency_overrides.clear()

    assert admin.json() == {"transaction_id": "txn_new"}
    assert viewer.status_code == 403
    assert made == [(COMPANY_ID, 45, "bob", "de")]


def test_an_admin_learns_why_their_payment_failed_and_a_viewer_doesnt(client, monkeypatch):
    """Billing decides the reason and refuses a transaction that isn't the buyer's (its 404
    passes through); a viewer never reaches billing."""
    asked = []

    async def failure(company_id, transaction_id, buyer_id):
        asked.append((company_id, transaction_id, buyer_id))

        if transaction_id != "txn_ours":
            raise HTTPException(404, "Not found")

        return "card_declined"

    monkeypatch.setattr(billing, "company_payment_failure", failure)
    path = f"{COMPANY}/billing/payment-failure"
    as_member(monkeypatch, "admin")
    ours = client.get(path, params={"transaction_id": "txn_ours"})
    theirs = client.get(path, params={"transaction_id": "txn_theirs"})
    as_member(monkeypatch, "viewer")
    viewer = client.get(path, params={"transaction_id": "txn_ours"})
    app.dependency_overrides.clear()

    assert ours.json() == {"reason": "card_declined"}
    assert theirs.status_code == 404
    assert viewer.status_code == 403
    assert asked == [(COMPANY_ID, "txn_ours", "bob"), (COMPANY_ID, "txn_theirs", "bob")]


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "checkout", {"candidates": 45}),
        ("GET", "payment-failure?transaction_id=txn_ours", None),
        ("GET", "invoice?transaction_id=txn_01", None),
    ],
)
def test_calls_to_paddle_stop_at_the_users_hourly_limit(client, monkeypatch, method, path, body):
    counted = []

    async def over(redis, key, name, **whose):
        counted.append((key, name))

        raise HTTPException(429, "Too many requests. Try again later.")

    async def never(*args):
        raise AssertionError("billing was called past the limit")

    monkeypatch.setattr(billing_routes, "hit_or_skip", over)
    monkeypatch.setattr(billing_prices, "company_checkout", never)
    monkeypatch.setattr(billing, "company_payment_failure", never)
    monkeypatch.setattr(billing, "company_invoice", never)
    as_member(monkeypatch, "admin")

    response = client.request(method, f"{COMPANY}/billing/{path}", json=body)
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert counted == [("rate:checkout-calls:bob", "CHECKOUT_CALLS_PER_USER_HOUR")]
