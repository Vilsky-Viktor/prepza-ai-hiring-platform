import asyncio

import pytest

from app.services import adjustments, webhooks
from app.storage import purchases, referrals
from tests.unit.paddle_events import adjustment


@pytest.fixture
def moved(monkeypatch):
    calls = []

    async def bought(transaction_id):
        # $10 paid for 1,000 credits.
        return ("company", "acme", 1_000, 1000)

    taken = {}

    async def take_back_credits(
        owner_type,
        owner_id,
        amount,
        transaction_id,
        adjustment_id,
        reason,
        total,
        currency,
        events=(),
    ):
        calls.append((owner_id, amount, f"adjustment:{transaction_id}:{adjustment_id}", reason))
        taken[transaction_id] = taken.get(transaction_id, 0) - amount

        return taken[transaction_id]

    async def take_back(transaction_id):
        calls.append(("referral taken back", transaction_id))

        return False

    monkeypatch.setattr(purchases, "for_transaction", bought)
    monkeypatch.setattr(purchases, "take_back", take_back_credits)
    monkeypatch.setattr(referrals, "take_back", take_back)

    return calls


def test_an_approved_refund_takes_the_credits_back(moved):
    asyncio.run(webhooks.handle(adjustment()))

    assert moved == [
        ("acme", -1_000, "adjustment:txn_01:adj_01", "refund"),
        ("referral taken back", "txn_01"),
    ]


def test_a_refund_keeps_the_money_it_returned(monkeypatch):
    kept = []

    async def bought(transaction_id):
        return ("company", "acme", 1_000, 1000)

    async def take_back_credits(owner_type, owner_id, amount, *rest):
        kept.append(rest[-3:-1])

        return 0

    monkeypatch.setattr(purchases, "for_transaction", bought)
    monkeypatch.setattr(purchases, "take_back", take_back_credits)

    asyncio.run(webhooks.handle(adjustment(total="250")))

    assert kept == [("250", "USD")]


def test_a_partial_refund_takes_back_its_share(moved):
    asyncio.run(webhooks.handle(adjustment(total="250")))

    assert moved == [("acme", -250, "adjustment:txn_01:adj_01", "refund")]


def test_partial_refunds_adding_up_to_the_whole_top_up_take_back_the_referral(moved):
    asyncio.run(webhooks.handle(adjustment(total="400", adjustment_id="adj_a")))
    asyncio.run(webhooks.handle(adjustment(total="600", adjustment_id="adj_b")))

    assert moved == [
        ("acme", -400, "adjustment:txn_01:adj_a", "refund"),
        ("acme", -600, "adjustment:txn_01:adj_b", "refund"),
        ("referral taken back", "txn_01"),
    ]


def test_a_chargeback_takes_back_and_its_reversal_returns(moved):
    asyncio.run(webhooks.handle(adjustment(action="chargeback", adjustment_id="adj_cb")))
    asyncio.run(webhooks.handle(adjustment(action="chargeback_reverse", adjustment_id="adj_rv")))

    assert [call[1] for call in moved] == [-1_000, "txn_01", 1_000]


@pytest.mark.parametrize(
    "event",
    [
        adjustment(status="pending_approval"),
        adjustment(status="rejected"),
        adjustment(action="chargeback_warning"),
        adjustment(action="credit"),
    ],
)
def test_nothing_moves_for_pending_rejected_or_other_adjustments(moved, event):
    asyncio.run(webhooks.handle(event))

    assert moved == []


def test_never_more_than_was_paid():
    assert adjustments.share(1_000, "5000", 1000) == 1_000
    assert adjustments.share(26_250, "12500", 25000) == 13_125
