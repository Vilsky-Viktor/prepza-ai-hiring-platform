"""Companies asks billing about a person's top-ups and a candidate's credits, for the admin
zone's support tab; storage faked."""

from datetime import UTC, datetime
from types import SimpleNamespace

from prepza_common.http.http import bearer

from billing.constants.products import MAX_BUYER_PURCHASES
from billing.core.security import service_token
from billing.repositories import ledger, purchases

AUTH = bearer(service_token("billing"))
NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


def test_a_persons_top_ups_newest_first(client, monkeypatch):
    asked = []

    async def bought_by(session, user_id, limit):
        asked.append((user_id, limit))
        row = SimpleNamespace(
            transaction_id="txn_01", owner_id="acme", total="5000", currency="USD", created_at=NOW
        )

        return [row] if user_id == "ann" else []

    monkeypatch.setattr(purchases, "bought_by", bought_by)
    response = client.get("/internal/purchases", params={"buyer_id": "ann"}, headers=AUTH)

    assert response.json() == [
        {
            "transaction_id": "txn_01",
            "company_id": "acme",
            "total": "5000",
            "currency": "USD",
            "created_at": "2026-10-10T12:00:00Z",
        }
    ]
    assert client.get("/internal/purchases", params={"buyer_id": "bob"}, headers=AUTH).json() == []
    assert asked == [("ann", MAX_BUYER_PURCHASES), ("bob", MAX_BUYER_PURCHASES)]


def test_a_candidates_credits_by_the_key_companies_gave_them(client, monkeypatch):
    async def hold_status(session, key):
        return "charged" if key == "candidate:interview-1:abc" else None

    monkeypatch.setattr(ledger, "hold_status", hold_status)
    found = client.get("/internal/candidates/hold", params={"key": "interview-1:abc"}, headers=AUTH)
    missing = client.get("/internal/candidates/hold", params={"key": "other"}, headers=AUTH)

    assert (found.status_code, found.json()) == (200, {"status": "charged"})
    assert missing.status_code == 404


def test_only_services_ask(client):
    assert client.get("/internal/purchases", params={"buyer_id": "ann"}).status_code == 401
    assert client.get("/internal/candidates/hold", params={"key": "k"}).status_code == 401
