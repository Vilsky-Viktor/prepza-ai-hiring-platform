"""The admin zone's support routes: superadmins only, billing faked over HTTP."""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
from prepza_common.http import http

from companies.integrations import accounts, billing
from companies.models.companies import Company, Member
from companies.repositories import companies, members

COMPANY_ID = uuid.uuid4()
URL = f"/superadmin/support/companies/{COMPANY_ID}"
ADJUSTMENT = {"amount": -500, "note": " Complaint 12: charged twice ", "key": str(uuid.uuid4())}
BELOW_ZERO = "That would take the available balance below zero."


@pytest.fixture
def acme(monkeypatch):
    company = Company(
        id=COMPANY_ID,
        name="Acme",
        verification_status="approved",
        verified_domain="acme.com",
        created_at=datetime(2026, 10, 1, tzinfo=UTC),
    )

    async def get(session, company_id):
        return company if company_id == COMPANY_ID else None

    async def list_for_company(session, company_id, offset, limit):
        return [Member(invited_email="ann@acme.com", role="owner", user_id="ann")]

    monkeypatch.setattr(companies, "get", get)
    monkeypatch.setattr(members, "list_for_company", list_for_company)


@pytest.fixture
def billing_answers(monkeypatch):
    """Billing over HTTP: `answers` maps a path to its status and body; the requests it got are
    kept."""
    answers, asked = {}, []

    def answer(request):
        asked.append((request.url.path, json.loads(request.content or "null")))
        code, body = answers[request.url.path]

        return httpx.Response(code, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)

    return SimpleNamespace(answers=answers, asked=asked)


def test_everyone_but_a_superadmin_finds_no_support_routes(client, superadmin, acme):
    superadmin("bob@example.com")

    assert client.post("/superadmin/support/search", json={"query": "acme"}).status_code == 404

    for path in ("", "/history", "/reserved", "/interviews", "/audit"):
        assert client.get(f"{URL}{path}").status_code == 404

    assert client.get(f"{URL}/invoice", params={"transaction_id": "txn_01"}).status_code == 404
    assert client.post(f"{URL}/adjustments", json=ADJUSTMENT).status_code == 404


def test_a_superadmin_sees_a_companys_people_and_credits(client, superadmin, acme, monkeypatch):
    async def company_credits(company_id):
        return {"balance": 1500, "reserved": 500, "available": 1000, "low": False}

    monkeypatch.setattr(billing, "company_credits", company_credits)
    superadmin("ann@example.com")

    assert client.get(URL).json() == {
        "id": str(COMPANY_ID),
        "name": "Acme",
        "verification_status": "approved",
        "verified_domain": "acme.com",
        "suspended": False,
        "created_at": "2026-10-01T00:00:00Z",
        "members": [{"email": "ann@acme.com", "role": "owner", "user_id": "ann"}],
        "balance": 1500,
        "reserved": 500,
    }
    assert client.get(f"/superadmin/support/companies/{uuid.uuid4()}").status_code == 404


def test_a_superadmins_adjustment_goes_to_billing_once_with_its_note(
    client, superadmin, acme, billing_answers
):
    billing_answers.answers[f"/internal/companies/{COMPANY_ID}/adjustments"] = (204, None)
    superadmin("ann@example.com")

    assert client.post(f"{URL}/adjustments", json=ADJUSTMENT).status_code == 204
    assert billing_answers.asked == [
        (
            f"/internal/companies/{COMPANY_ID}/adjustments",
            {"amount": -500, "note": "Complaint 12: charged twice", "key": ADJUSTMENT["key"]},
        )
    ]


def test_billings_refusal_of_an_adjustment_reaches_the_superadmin(
    client, superadmin, acme, billing_answers
):
    billing_answers.answers[f"/internal/companies/{COMPANY_ID}/adjustments"] = (
        409,
        {"detail": BELOW_ZERO},
    )
    superadmin("ann@example.com")
    response = client.post(f"{URL}/adjustments", json=ADJUSTMENT)

    assert (response.status_code, response.json()) == (409, {"detail": BELOW_ZERO})


def test_a_gone_company_is_not_adjusted(client, superadmin, acme, billing_answers):
    superadmin("ann@example.com")
    response = client.post(
        f"/superadmin/support/companies/{uuid.uuid4()}/adjustments", json=ADJUSTMENT
    )

    assert response.status_code == 404
    assert billing_answers.asked == []


def test_an_unknown_transaction_has_no_owner(billing_answers):
    billing_answers.answers["/internal/purchases/txn_01"] = (404, {"detail": "Not found"})
    billing_answers.answers["/internal/purchases/txn_02"] = (
        200,
        {"owner_type": "company", "owner_id": "acme"},
    )

    assert asyncio.run(billing.purchase_owner("txn_01")) is None
    assert asyncio.run(billing.purchase_owner("txn_02")) == {
        "owner_type": "company",
        "owner_id": "acme",
    }


def test_only_what_could_be_an_account_id_is_asked_of_accounts(billing_answers):
    """Anything else, a path above all, never reaches accounts as one."""
    billing_answers.answers["/internal/accounts/uid-ann"] = (200, {"user_id": "uid-ann"})
    billing_answers.answers["/internal/accounts/gone"] = (404, {"detail": "Not found"})

    assert asyncio.run(accounts.account("uid-ann")) == {"user_id": "uid-ann"}
    assert asyncio.run(accounts.account("gone")) is None
    assert asyncio.run(accounts.account("../users/ids")) is None
    assert asyncio.run(accounts.account("acme corp")) is None
    assert [path for path, _ in billing_answers.asked] == [
        "/internal/accounts/uid-ann",
        "/internal/accounts/gone",
    ]


def test_an_address_is_looked_up_in_the_body(billing_answers):
    billing_answers.answers["/internal/accounts/lookup"] = (404, {"detail": "Not found"})

    assert asyncio.run(accounts.account_by_email("ann@example.com")) is None
    assert billing_answers.asked == [("/internal/accounts/lookup", {"email": "ann@example.com"})]


def test_a_candidate_never_held_has_no_credits_state(billing_answers):
    billing_answers.answers["/internal/candidates/hold"] = (404, {"detail": "Not found"})

    assert asyncio.run(billing.candidate_hold("key-1")) is None

    billing_answers.answers["/internal/candidates/hold"] = (200, {"status": "open"})

    assert asyncio.run(billing.candidate_hold("key-1")) == "open"
