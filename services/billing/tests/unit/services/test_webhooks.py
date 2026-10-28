import asyncio
import time

import pytest
from prepza_common.config.constants import WEBHOOK_SIGNATURE_REFUSED

from billing.constants.products import WEBHOOK_TOLERANCE_SECONDS
from billing.helpers.paddle import signature_valid
from billing.repositories import auto_top_ups, purchases, referrals
from billing.services import webhooks
from tests.unit.paddle_events import SECRET, completed, signed


def test_a_signature_from_paddle_is_valid():
    body, header = signed(completed())

    assert signature_valid(header, body, SECRET, time.time(), WEBHOOK_TOLERANCE_SECONDS)


def test_during_a_secret_rotation_one_matching_signature_is_enough():
    body, header = signed(completed())
    timestamp, h1 = header.split(";")

    assert signature_valid(
        f"{timestamp};h1=from-the-other-secret;{h1}", body, SECRET, time.time(), 300
    )


@pytest.mark.parametrize(
    "case", ["wrong secret", "old", "tampered body", "no secret configured", "garbage header"]
)
def test_other_signatures_are_refused(case):
    body, header = signed(completed(), secret="other" if case == "wrong secret" else SECRET)
    secret = "" if case == "no secret configured" else SECRET
    now = time.time() + (WEBHOOK_TOLERANCE_SECONDS + 1 if case == "old" else 0)

    if case == "tampered body":
        body = body.replace(b"acme", b"evil")

    if case == "garbage header":
        header = "nonsense"

    assert not signature_valid(header, body, secret, now, WEBHOOK_TOLERANCE_SECONDS)


@pytest.fixture
def granted(monkeypatch):
    calls = []

    async def fake_grant(
        session,
        owner_type,
        owner_id,
        credits,
        quantity,
        transaction_id,
        product,
        buyer_id,
        total,
        currency,
        now,
        automatic=False,
        events=(),
    ):
        calls.append((transaction_id, product, quantity, credits, owner_id, buyer_id))

        return True

    async def no_referral(session, owner_type, owner_id, transaction_id, events_for=None):
        return None

    monkeypatch.setattr(purchases, "grant", fake_grant)
    monkeypatch.setattr(referrals, "reward", no_referral)

    return calls


@pytest.mark.parametrize(
    ("currency", "subtotal"), [("USD", "5000"), ("EUR", "5000"), ("GBP", "4000")]
)
def test_a_completed_transaction_grants_the_same_candidates_in_any_currency(
    granted, currency, subtotal
):
    event = completed(quantity=2, currency=currency, subtotal=subtotal)

    asyncio.run(webhooks.handle(event))

    assert granted == [("txn_01", "topup_50", 2, 10_000, "acme", "ann")]


@pytest.fixture
def money(monkeypatch):
    """What each grant keeps on its history entry: the money paid and whether it was automatic."""
    kept = []

    async def fake_grant(session, *args):
        kept.append(args[7:9] + args[10:11])

        return True

    async def no_referral(session, owner_type, owner_id, transaction_id, events_for=None):
        return None

    async def owner_of(session, subscription_id):
        return ("company", "acme")

    monkeypatch.setattr(purchases, "grant", fake_grant)
    monkeypatch.setattr(referrals, "reward", no_referral)
    monkeypatch.setattr(auto_top_ups, "owner_of", owner_of)

    return kept


def test_a_top_up_keeps_what_it_cost_and_an_automatic_one_says_so(money, monkeypatch):
    automatic = completed(currency="GBP")
    automatic["data"]["subscription_id"] = "sub_01"
    automatic["data"]["details"]["totals"]["grand_total"] = "4800"

    async def started(custom, subscription_id, currency):
        return None

    monkeypatch.setattr(webhooks.auto_top_ups, "start", started)

    asyncio.run(webhooks.handle(completed()))
    asyncio.run(webhooks.handle(automatic))

    assert money == [("5000", "USD", False), ("4800", "GBP", True)]


@pytest.mark.parametrize(
    "event",
    [
        completed(product_id="pro_other"),
        completed(top_up="topup_7"),
        completed(candidates=9),
        completed(candidates=1_001),
        {**completed(), "event_type": "transaction.created"},
        completed(owner_id=None),
    ],
    ids=["another product", "unknown top-up", "too few", "too many", "other event", "no owner"],
)
def test_anything_else_grants_nothing(granted, event):
    asyncio.run(webhooks.handle(event))

    assert granted == []


def test_the_webhook_route_checks_the_signature(client, granted, caplog):
    body, header = signed(completed())

    ok = client.post("/webhooks/paddle", content=body, headers={"Paddle-Signature": header})
    forged = client.post(
        "/webhooks/paddle", content=body, headers={"Paddle-Signature": header + "0"}
    )

    assert ok.status_code == 200
    assert forged.status_code == 401
    assert len(granted) == 1
    # Logged as an error, which the alert for a wrong web hook secret matches.
    assert [r.levelname for r in caplog.records if WEBHOOK_SIGNATURE_REFUSED in r.message] == [
        "ERROR"
    ]


def test_a_signature_beyond_ascii_is_refused_not_an_error():
    assert signature_valid("ts=1000;h1=ä", b"{}", SECRET, 1000, WEBHOOK_TOLERANCE_SECONDS) is False
