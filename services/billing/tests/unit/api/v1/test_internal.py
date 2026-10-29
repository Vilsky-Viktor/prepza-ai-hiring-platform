import asyncio
from types import SimpleNamespace

from prepza_common.http.http import bearer

from billing.constants.credits import CANDIDATE_CREDITS
from billing.core.security import service_token
from billing.repositories import auto_top_ups as auto_top_up_rows
from billing.repositories import ledger, purchases
from billing.services import auto_top_up_charging, auto_top_ups

AUTH = bearer(service_token("billing"))
HOLD = {"company_id": "acme", "key": "session-1"}


def test_a_candidate_without_enough_credits_is_refused_with_a_message(client, monkeypatch):
    async def too_low(session, owner_type, owner_id, amount, key, reason):
        return False

    monkeypatch.setattr(ledger, "reserve", too_low)

    response = client.post("/internal/candidates/hold", params=HOLD, headers=AUTH)

    assert response.status_code == 402
    assert response.json() == {"detail": "Not enough credits. Top up to continue."}


def test_a_candidate_holds_its_credits_and_a_top_up_is_checked_before_answering(
    client, monkeypatch
):
    """Nothing runs after the answer (Cloud Run slows the CPU then): the top-up is checked
    first."""
    done = []

    async def reserve(session, owner_type, owner_id, amount, key, reason):
        done.append(("held", owner_id, amount, key))

        return True

    async def check(owner_type, owner_id):
        done.append(("top-up checked", owner_id))

    monkeypatch.setattr(ledger, "reserve", reserve)
    monkeypatch.setattr(auto_top_up_charging, "check", check)

    response = client.post("/internal/candidates/hold", params=HOLD, headers=AUTH)

    assert response.status_code == 204
    assert done == [
        ("held", "acme", CANDIDATE_CREDITS, "candidate:session-1"),
        ("top-up checked", "acme"),
    ]


def test_a_slow_top_up_is_cut_off_and_the_hold_still_answers(client, monkeypatch):
    """Paddle can take its time: the invite waiting on the hold waits for it only briefly."""
    cut_off = []

    async def reserve(session, owner_type, owner_id, amount, key, reason):
        return True

    async def never_answers(owner_type, owner_id):
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cut_off.append(owner_id)
            raise

    monkeypatch.setattr(ledger, "reserve", reserve)
    monkeypatch.setattr(auto_top_up_charging, "check", never_answers)
    monkeypatch.setattr(auto_top_up_charging, "AUTO_TOP_UP_WAIT_SECONDS", 0.01)

    response = client.post("/internal/candidates/hold", params=HOLD, headers=AUTH)

    assert response.status_code == 204
    assert cut_off == ["acme"]


def test_several_companies_balances_at_once(client, monkeypatch):
    async def found(session, owner_type, owner_ids):
        return {"a": SimpleNamespace(owner_type="company", balance=1500, reserved=500)}

    monkeypatch.setattr(ledger, "wallets", found)

    response = client.post(
        "/internal/companies/credits", json={"owner_ids": ["a", "b"]}, headers=AUTH
    )

    assert response.json() == {
        "a": {"balance": 1500, "reserved": 500, "available": 1000, "low": False, "candidates": 2},
        "b": {"balance": 0, "reserved": 0, "available": 0, "low": True, "candidates": 0},
    }


def test_a_removed_members_card_turns_off_only_their_auto_top_up(client, monkeypatch):
    calls = []

    async def turn_off(owner_type, owner_id, buyer_id=None):
        calls.append((owner_type, owner_id, buyer_id))

    monkeypatch.setattr(auto_top_ups, "turn_off", turn_off)

    response = client.delete(
        "/internal/companies/acme/auto-top-up", params={"buyer_id": "ann"}, headers=AUTH
    )

    assert response.status_code == 204
    assert calls == [("company", "acme", "ann")]


def test_accounts_exports_a_users_purchases_and_automatic_top_ups_with_a_post(client, monkeypatch):
    """The export is a POST, like every service's, so accounts sends nothing in the URL. An
    automatic top-up the user turned on charges their card, so it's theirs to see too."""

    async def purchases_of(session, user_id):
        return []

    async def of_buyer(session, buyer_id):
        return [
            SimpleNamespace(
                owner_id="acme",
                product="topup_50",
                threshold=500,
                subscription_id="sub_1",
                charged_at=None,
                failed_at=None,
            )
        ]

    monkeypatch.setattr(purchases, "purchases_of", purchases_of)
    monkeypatch.setattr(auto_top_up_rows, "of_buyer", of_buyer)

    response = client.post("/internal/users/ann/export", headers=AUTH)

    assert response.json() == {
        # Never chosen nor seen with a country: none saved.
        "currency": None,
        "auto_top_ups": [
            {
                "company_id": "acme",
                "product": "topup_50",
                "threshold": 500,
                "started": True,
                "last_charged_at": None,
                "last_declined_at": None,
            }
        ],
        "purchases": [],
    }


def test_low_companies_say_how_many_credits_are_available(client, monkeypatch):
    asked = []

    async def running_low(session, owner_type, owner_ids=None, after="", limit=None):
        asked.append(owner_ids)

        return [SimpleNamespace(owner_id="acme", balance=1400, reserved=300)]

    monkeypatch.setattr(ledger, "running_low", running_low)

    response = client.get("/internal/companies/low", headers=AUTH)

    assert response.json() == {
        "companies": [{"company_id": "acme", "available": 1100, "candidates": 2}]
    }
    assert asked == [None]


def test_low_companies_can_be_only_those_asked_for(client, monkeypatch):
    asked = []

    async def running_low(session, owner_type, owner_ids=None, after="", limit=None):
        asked.append(owner_ids)

        return []

    monkeypatch.setattr(ledger, "running_low", running_low)

    response = client.get("/internal/companies/low?ids=a&ids=b", headers=AUTH)

    assert response.json() == {"companies": []}
    assert asked == [["a", "b"]]
