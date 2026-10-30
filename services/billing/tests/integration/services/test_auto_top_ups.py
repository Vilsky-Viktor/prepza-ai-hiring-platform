import uuid
from datetime import UTC, datetime

from fastapi import HTTPException

from billing.constants.credits import CANDIDATE_CREDITS, WELCOME_COMPANY, Reason
from billing.constants.currencies import Currency
from billing.constants.products import AUTO_TOP_UP_COOLDOWN, OwnerType
from billing.repositories import auto_top_ups as rows
from billing.repositories import ledger
from billing.schemas.billing import AutoTopUpIn
from billing.services import accounts, auto_top_ups
from billing.services.topups import handle_completed
from tests.integration.conftest import charged
from tests.integration.factories import welcomed
from tests.integration.transactions import transaction

COMPANY = OwnerType.COMPANY


def checkout_data(owner_id, buyer_id):
    return {"owner_type": COMPANY, "owner_id": owner_id, "buyer_id": buyer_id, "auto_top_up": "1"}


def test_turning_on_waits_for_the_checkout_then_refills_under_the_threshold_once(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        waiting = await auto_top_ups.turn_on(
            COMPANY,
            acme,
            AutoTopUpIn(product="topup_50", threshold=500, agreed=True),
            ann,
            Currency.USD,
        )
        # Someone else's checkout can't start it; the owner's does, once.
        await auto_top_ups.start(checkout_data(acme, "mallory"), "sub_other", "USD")
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        started = await auto_top_ups.out(COMPANY, acme, Currency.USD)
        # The welcome credits aren't under 500, so nothing is charged. Inviting candidates takes
        # them under: one charge, however often it's checked, while its credits haven't come.
        await auto_top_ups.check(COMPANY, acme)
        await transaction(
            ledger.reserve, COMPANY, acme, WELCOME_COMPANY - 1, "candidate:x", Reason.CANDIDATE
        )
        await auto_top_ups.check(COMPANY, acme)
        await auto_top_ups.check(COMPANY, acme)
        later = await transaction(
            rows.claim_charge, COMPANY, acme, datetime.now(UTC) + AUTO_TOP_UP_COOLDOWN * 2
        )

        return waiting, started, later

    waiting, started, later = run(scenario())

    # The card's checkout is a transaction billing made, in the company's currency.
    assert waiting.checkout.transaction_id == f"txn_pri_plan_USD_{ann}"
    assert not waiting.on and waiting.waiting
    assert started.on and started.product == "topup_50" and started.threshold == 500
    assert paddle_calls == [
        ("cancel", "sub_other"),
        ("charge", sub, "topup_50", "5000", "USD"),
    ]
    assert later is None


def test_turning_off_cancels_the_subscription_and_choices_are_checked(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await auto_top_ups.turn_on(
            COMPANY,
            acme,
            AutoTopUpIn(product="topup_50", threshold=500, agreed=True),
            ann,
            Currency.USD,
        )
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        await auto_top_ups.turn_off(COMPANY, acme)
        refused = []

        for body in (
            AutoTopUpIn(product="topup_50", threshold=123, agreed=True),
            AutoTopUpIn(product="topup_7", threshold=500, agreed=True),
        ):
            try:
                await auto_top_ups.turn_on(COMPANY, acme, body, ann, Currency.USD)
            except HTTPException as error:
                refused.append(error.status_code)

        return await auto_top_ups.out(COMPANY, acme, Currency.USD), refused

    after, refused = run(scenario())

    assert not after.on and not after.waiting
    assert paddle_calls == [("cancel", sub)]
    assert refused == [422, 422]


def test_an_automatic_charge_credits_the_wallet_its_subscription_belongs_to(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    card = {
        "id": f"txn_{uuid.uuid4().hex[:12]}",
        "subscription_id": sub,
        "currency_code": "GBP",
        "custom_data": checkout_data(acme, ann),
        "items": [{"price": {"id": "pri_plan"}, "quantity": 1}],
        "details": {"totals": {"grand_total": "0"}},
    }

    async def scenario():
        await auto_top_ups.turn_on(
            COMPANY,
            acme,
            AutoTopUpIn(product="topup_50", threshold=500, agreed=True),
            ann,
            Currency.USD,
        )
        # The $0 checkout starts it and buys nothing; the charge carries no custom data.
        await handle_completed(card)
        opened = await transaction(ledger.wallet, COMPANY, acme)
        # Charged in pounds: the same 10 candidates as in dollars.
        await handle_completed(charged(sub, currency="GBP", subtotal="4000"))

        return opened.balance, (await transaction(ledger.wallet, COMPANY, acme)).balance

    opened, after = run(scenario())

    assert opened == 0
    assert after == 10 * CANDIDATE_CREDITS


def test_the_same_subscription_twice_stays_attached_and_a_deleted_buyer_turns_it_off(
    run, paddle_calls
):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await auto_top_ups.turn_on(
            COMPANY,
            acme,
            AutoTopUpIn(product="topup_50", threshold=500, agreed=True),
            ann,
            Currency.USD,
        )
        # Paddle's two events for one checkout, handled at the same moment.
        first = await transaction(rows.start, COMPANY, acme, ann, sub, "USD")
        second = await transaction(rows.start, COMPANY, acme, ann, sub, "USD")
        # The buyer deletes their account: their card is never charged again.
        await accounts.delete_user(ann)

        return first, second, await auto_top_ups.out(COMPANY, acme, Currency.USD)

    first, second, after = run(scenario())

    assert first and second
    assert not after.on and not after.waiting
    assert paddle_calls == [("cancel", sub)]


def test_a_removed_member_turns_it_off_only_when_their_card_pays(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    bob = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await auto_top_ups.turn_on(
            COMPANY,
            acme,
            AutoTopUpIn(product="topup_50", threshold=500, agreed=True),
            ann,
            Currency.USD,
        )
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        # Bob didn't turn it on: removing him leaves it running.
        await auto_top_ups.turn_off(COMPANY, acme, bob)
        kept = await auto_top_ups.out(COMPANY, acme, Currency.USD)
        await auto_top_ups.turn_off(COMPANY, acme, ann)

        return kept, await auto_top_ups.out(COMPANY, acme, Currency.USD)

    kept, after = run(scenario())

    assert kept.on
    assert not after.on and not after.waiting
    assert paddle_calls == [("cancel", sub)]
