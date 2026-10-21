import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.constants.credits import WELCOME_COMPANY, Reason
from app.constants.currencies import Currency
from app.constants.products import (
    AUTO_TOP_UP_COOLDOWN,
    AUTO_TOP_UP_RETRY_AFTER,
    AUTO_TOP_UP_UNCREDITED_WAIT,
    OwnerType,
)
from app.schemas.billing import AutoTopUpIn
from app.services import auto_top_ups
from app.storage import auto_top_ups as rows
from app.storage import ledger
from tests.integration.test_auto_top_ups import checkout_data

COMPANY = OwnerType.COMPANY
CHOICE = AutoTopUpIn(product="topup_50", threshold=500)


def test_a_second_member_turning_it_on_before_the_first_checkout_starts_it_with_their_card(
    run, paddle_calls
):
    ann, bob = f"user-{uuid.uuid4()}", f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        waiting = await auto_top_ups.turn_on(COMPANY, acme, CHOICE, bob, Currency.USD)
        await auto_top_ups.start(checkout_data(acme, bob), sub, "USD")

        # Once running on Bob's card, only Bob changes it: Ann is refused, and it runs as before.
        with pytest.raises(HTTPException) as refused:
            await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)

        return (
            waiting,
            refused.value.status_code,
            await auto_top_ups.out(COMPANY, acme, Currency.USD),
            await rows.get(COMPANY, acme),
        )

    waiting, refused, after, row = run(scenario())

    assert waiting.checkout.transaction_id.endswith(bob)
    assert refused == 403
    assert after.on
    assert row.buyer_id == bob
    assert paddle_calls == []


def test_a_subscription_that_ended_before_its_checkout_arrived_isnt_started(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_ended_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        # subscription.canceled came first and found nothing to turn off.
        await auto_top_ups.ended(sub)
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")

        return await auto_top_ups.out(COMPANY, acme, Currency.USD)

    after = run(scenario())

    assert not after.on and after.waiting


def test_a_declined_card_is_tried_again_only_after_a_day_or_a_new_save(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_declined_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        await ledger.reserve(
            COMPANY, acme, WELCOME_COMPANY - 1, f"candidate:{acme}", Reason.CANDIDATE
        )
        await auto_top_ups.check(COMPANY, acme)
        soon = await rows.claim_charge(
            COMPANY, acme, datetime.now(UTC) + AUTO_TOP_UP_RETRY_AFTER / 2
        )
        next_day = await rows.claim_charge(
            COMPANY, acme, datetime.now(UTC) + AUTO_TOP_UP_RETRY_AFTER * 2
        )
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        saved = await rows.get(COMPANY, acme)

        return soon, next_day, saved

    soon, next_day, saved = run(scenario())

    assert [call[0] for call in paddle_calls] == ["charge"]
    assert soon is None
    assert next_day is not None
    assert saved.failed_at is None


def test_a_charge_that_timed_out_isnt_failed_and_is_tried_again_only_after_a_day(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_timeout_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        await ledger.reserve(
            COMPANY, acme, WELCOME_COMPANY - 1, f"candidate:{acme}", Reason.CANDIDATE
        )
        # Paddle may have taken it: its web hook would add the credits.
        await auto_top_ups.check(COMPANY, acme)
        row = await rows.get(COMPANY, acme)
        # Its credits never came: no charge after the cooldown, only after a day.
        soon = await rows.claim_charge(COMPANY, acme, datetime.now(UTC) + AUTO_TOP_UP_COOLDOWN * 2)
        next_day = await rows.claim_charge(
            COMPANY, acme, datetime.now(UTC) + AUTO_TOP_UP_UNCREDITED_WAIT * 2
        )

        return row, soon, next_day

    row, soon, next_day = run(scenario())

    assert [call[0] for call in paddle_calls] == ["charge"]
    assert row.failed_at is None
    assert soon is None
    assert next_day is not None
