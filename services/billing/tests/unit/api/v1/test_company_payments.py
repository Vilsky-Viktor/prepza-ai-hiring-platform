"""A company's payment routes in billing: billing asks companies who the user is in the company
(members look, owners and admins pay), passes the visitor's country and interface language on,
and counts calls to Paddle against the user's hourly limit."""

import uuid

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.http import http

from billing.main import app
from billing.schemas.billing import CompanyCurrencyOut, InvoiceOut, TopUpCheckoutOut
from billing.services import checkout_calls, checkouts, currencies, invoices, payment_failures

COMPANY_ID = uuid.uuid4()
COMPANY = f"/companies/{COMPANY_ID}/billing"
# Paddle transaction ids (TRANSACTION_ID_PATTERN): ours and someone else's.
OURS = "txn_" + "a" * 26
THEIRS = "txn_" + "b" * 26
ROLES = {
    "owner": {"member": True, "editor": True},
    "viewer": {"member": True, "editor": False},
    "stranger": {"member": False, "editor": False},
    "suspended": {"member": True, "editor": True, "read_only": "The company is suspended"},
}


@pytest.fixture
def asked(monkeypatch):
    """Companies, faked: answers who "owner", "viewer", "stranger" and "suspended" are in the
    company; records each access check (company, user, the X-Assistant header passed on)."""
    checks = []

    def answer(request):
        user_id = request.url.params["user_id"]
        checks.append((request.url.path, user_id, request.headers.get("X-Assistant")))

        return httpx.Response(200, json=ROLES[user_id])

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)

    yield checks

    app.dependency_overrides.clear()


@pytest.fixture
def counted(monkeypatch):
    """The calls counted against the user's hourly limit of calls to Paddle."""
    keys = []

    async def hit(redis, key, name, **whose):
        keys.append((key, name))

    monkeypatch.setattr(checkout_calls, "hit_or_skip", hit)

    return keys


def sign_in(user_id):
    app.dependency_overrides[current_user] = lambda: User(
        uid=user_id, email=f"{user_id}@example.com", email_verified=True
    )


def test_an_owner_gets_a_checkout_billing_makes_in_their_language(
    client, asked, counted, monkeypatch
):
    made = []

    async def checkout(company_id, candidates, buyer_id, country, language):
        made.append((company_id, candidates, buyer_id, country, language))

        return TopUpCheckoutOut(transaction_id="txn_new")

    monkeypatch.setattr(checkouts, "company_checkout", checkout)
    sign_in("owner")

    response = client.post(
        f"{COMPANY}/checkout",
        json={"candidates": 45},
        headers={"Accept-Language": "de-DE", "X-Client-Country": "DE", "X-Assistant": "mcp"},
    )

    assert response.json() == {"transaction_id": "txn_new"}
    assert made == [(str(COMPANY_ID), 45, "owner", "DE", "de")]
    assert asked == [(f"/internal/companies/{COMPANY_ID}/access", "owner", "mcp")]
    assert counted == [("rate:checkout-calls:owner", "CHECKOUT_CALLS_PER_USER_HOUR")]


@pytest.mark.parametrize(
    ("user", "status"), [("viewer", 403), ("stranger", 404), ("suspended", 403)]
)
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/checkout", {"candidates": 45}),
        ("GET", "/catalog", None),
        ("PUT", "/currency", {"currency": "EUR"}),
        ("GET", f"/invoice?transaction_id={OURS}", None),
        ("GET", f"/payment-failure?transaction_id={OURS}", None),
    ],
)
def test_only_an_owner_or_admin_pays_or_reads_the_payments(
    client, asked, counted, user, status, method, path, body
):
    sign_in(user)

    response = client.request(method, f"{COMPANY}{path}", json=body)

    assert response.status_code == status
    # Refused before Paddle is called, so nothing is counted.
    assert counted == []


def test_any_member_reads_the_currency_and_a_pages_server_passes_its_visitors_country(
    client, asked, saved_currencies
):
    sign_in("viewer")

    # A page's server calls through the load balancer, which sets its own country in the header.
    response = client.get(f"{COMPANY}/currency?country=DE", headers={"X-Client-Country": "US"})
    sign_in("stranger")
    stranger = client.get(f"{COMPANY}/currency")

    assert response.json()["currency"] == "EUR"
    assert stranger.status_code == 404


def test_an_owner_chooses_the_currency_as_themselves(client, asked, monkeypatch):
    """The action log names who chose it (the integration tests check its line)."""
    chosen = []

    async def choose_company(company_id, currency, actor):
        chosen.append((company_id, currency, actor))

        return CompanyCurrencyOut(currency=currency)

    monkeypatch.setattr(currencies, "choose_company", choose_company)
    sign_in("owner")

    response = client.put(f"{COMPANY}/currency", json={"currency": "GBP"})
    refused = client.put(f"{COMPANY}/currency", json={"currency": "XYZ"})

    assert response.json()["currency"] == "GBP"
    assert refused.status_code == 422
    assert chosen == [(str(COMPANY_ID), "GBP", "owner")]


def test_an_invoice_and_a_failure_are_the_owners_own_transactions_only(
    client, asked, counted, monkeypatch
):
    async def invoice(company_id, transaction_id):
        if transaction_id != OURS:
            raise HTTPException(404, "Not found")

        return InvoiceOut(url="https://paddle.test/txn_01.pdf")

    async def failure(owner_type, company_id, buyer_id, transaction_id):
        return "card_declined" if transaction_id == OURS else None

    monkeypatch.setattr(invoices, "company_invoice", invoice)
    monkeypatch.setattr(payment_failures, "failure", failure)
    sign_in("owner")

    responses = [
        client.get(f"{COMPANY}/{path}", params={"transaction_id": transaction_id})
        for path in ("invoice", "payment-failure")
        for transaction_id in (OURS, THEIRS)
    ]

    assert [response.status_code for response in responses] == [200, 404, 200, 404]
    assert responses[0].json() == {"url": "https://paddle.test/txn_01.pdf"}
    assert responses[2].json() == {"reason": "card_declined"}


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/checkout", {"candidates": 45}),
        ("GET", f"/payment-failure?transaction_id={OURS}", None),
        ("GET", f"/invoice?transaction_id={OURS}", None),
    ],
)
def test_calls_to_paddle_stop_at_the_users_hourly_limit(
    client, asked, monkeypatch, method, path, body
):
    async def over(redis, key, name, **whose):
        raise HTTPException(429, "Too many requests. Try again later.")

    async def never(*args):
        raise AssertionError("Paddle was called past the limit")

    monkeypatch.setattr(checkout_calls, "hit_or_skip", over)
    monkeypatch.setattr(checkouts, "company_checkout", never)
    monkeypatch.setattr(payment_failures, "failure", never)
    monkeypatch.setattr(invoices, "company_invoice", never)
    sign_in("owner")

    assert client.request(method, f"{COMPANY}{path}", json=body).status_code == 429
