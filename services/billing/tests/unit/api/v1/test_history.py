import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.http.http import bearer

from billing.constants.credits import Reason
from billing.core.security import service_token
from billing.helpers.history import history_entry_out, transaction_id
from billing.integrations import paddle
from billing.models.billing import Entry
from billing.repositories import history, purchases

AUTH = bearer(service_token("billing"))
NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


def entry(key, reason, amount=100, **money):
    return Entry(
        id=uuid.uuid4(),
        key=key,
        owner_type="company",
        owner_id="acme",
        amount=amount,
        reason=reason,
        total_minor=money.get("total_minor"),
        currency=money.get("currency"),
        automatic=money.get("automatic", False),
        created_at=NOW,
    )


@pytest.mark.parametrize(
    ("key", "reason", "expected"),
    [
        ("txn_01:topup_50", Reason.TOPUP, "txn_01"),
        ("adjustment:txn_01:adj_01", Reason.REFUND, "txn_01"),
        ("adjustment:txn_01:adj_02", Reason.CHARGEBACK_REVERSED, "txn_01"),
        # Older adjustments carry only the adjustment.
        ("adjustment:adj_01", Reason.CHARGEBACK, None),
        ("candidate:abc", Reason.CANDIDATE, None),
        ("welcome:ann", Reason.WELCOME, None),
    ],
)
def test_a_top_up_or_adjustment_names_its_paddle_transaction(key, reason, expected):
    assert transaction_id(entry(key, reason)) == expected


def test_a_candidates_movement_carries_the_key_companies_knows_the_invite_by():
    legacy = history_entry_out(entry("candidate:interview-1:ann@example.com", Reason.CANDIDATE))
    current = history_entry_out(entry("candidate:hold-1", Reason.CANDIDATE))
    other = history_entry_out(entry("txn_01:topup_50", Reason.TOPUP))

    assert (legacy.hold_key, current.hold_key, other.hold_key) == (
        "interview-1:ann@example.com",
        "hold-1",
        None,
    )


def test_the_history_route_lists_a_page_with_the_money_and_transaction(client, monkeypatch):
    asked = []

    async def page(owner_type, owner_id, offset, limit):
        asked.append((owner_type, owner_id, offset, limit))

        return [
            entry(
                "txn_01:topup_50",
                Reason.TOPUP,
                3_000,
                total_minor=3000,
                currency="USD",
                automatic=True,
            ),
            entry("candidate:hold-1", Reason.CANDIDATE, -300),
        ]

    monkeypatch.setattr(history, "page", page)

    response = client.get(
        "/internal/companies/acme/history", params={"offset": 20, "limit": 10}, headers=AUTH
    )
    topup, candidate = response.json()

    assert asked == [("company", "acme", 20, 10)]
    assert (topup["amount"], topup["total"], topup["currency"], topup["automatic"]) == (
        3_000,
        "3000",
        "USD",
        True,
    )
    assert (topup["transaction_id"], topup["hold_key"]) == ("txn_01", None)
    assert (candidate["amount"], candidate["transaction_id"], candidate["hold_key"]) == (
        -300,
        None,
        "hold-1",
    )


@pytest.fixture
def invoices(monkeypatch):
    """The company acme owns txn_01 only; Paddle's invoice links, faked."""
    asked = []

    async def owns(owner_type, owner_id, transaction):
        return (owner_type, owner_id, transaction) == ("company", "acme", "txn_01")

    async def invoice_url(transaction):
        asked.append(transaction)

        return f"https://paddle.test/{transaction}.pdf"

    monkeypatch.setattr(purchases, "owns", owns)
    monkeypatch.setattr(paddle, "invoice_url", invoice_url)

    return asked


def test_a_companys_own_top_up_has_an_invoice(client, invoices):
    response = client.get(
        "/internal/companies/acme/invoice", params={"transaction_id": "txn_01"}, headers=AUTH
    )

    assert response.json() == {"url": "https://paddle.test/txn_01.pdf"}


def test_another_companys_transaction_is_not_found_and_paddle_isnt_asked(client, invoices):
    response = client.get(
        "/internal/companies/evil/invoice", params={"transaction_id": "txn_01"}, headers=AUTH
    )

    assert response.status_code == 404
    assert invoices == []


def test_the_history_and_invoice_need_a_service_token(client):
    assert client.get("/internal/companies/acme/history").status_code == 401
    assert (
        client.get(
            "/internal/companies/acme/invoice", params={"transaction_id": "txn_01"}
        ).status_code
        == 401
    )


def test_a_top_ups_transaction_says_whose_wallet_it_paid_into(client, monkeypatch):
    async def for_transaction(transaction):
        return ("company", "acme", 1_000, "1000") if transaction == "txn_01" else None

    monkeypatch.setattr(purchases, "for_transaction", for_transaction)

    found = client.get("/internal/purchases/txn_01", headers=AUTH)
    unknown = client.get("/internal/purchases/txn_02", headers=AUTH)

    assert found.json() == {"owner_type": "company", "owner_id": "acme"}
    assert unknown.status_code == 404
    assert client.get("/internal/purchases/txn_01").status_code == 401
