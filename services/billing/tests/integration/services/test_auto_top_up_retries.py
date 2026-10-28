"""A declined automatic top-up against Postgres: tried again after 1, 3 and 7 days, paused after a
fourth decline or at once for one that can't pass later, and resumed only by a card saved after
the pause."""

import uuid
from datetime import UTC, datetime, timedelta

from billing.constants.credits import WELCOME_COMPANY, Reason
from billing.constants.currencies import Currency
from billing.constants.declines import AUTO_TOP_UP_RETRY_WAITS
from billing.constants.products import OwnerType
from billing.repositories import auto_top_up_charges as charges
from billing.repositories import auto_top_ups as rows
from billing.repositories import ledger
from billing.schemas.billing import AutoTopUpIn
from billing.services import auto_top_ups
from tests.integration.services.test_auto_top_ups import checkout_data

COMPANY = OwnerType.COMPANY
CHOICE = AutoTopUpIn(product="topup_50", threshold=500)
DAY = timedelta(days=1)


async def running_low(acme: str, sub: str) -> None:
    """Acme's automatic top-up runs on Ann's card, and its balance is under the threshold."""
    ann = f"user-{uuid.uuid4()}"
    await ledger.welcome_company(acme, f"{acme}@example.com")
    await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
    await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
    await ledger.reserve(COMPANY, acme, WELCOME_COMPANY - 1, f"candidate:{acme}", Reason.CANDIDATE)


def test_soft_declines_are_tried_again_after_1_3_and_7_days_then_it_pauses(run, paddle_calls):
    acme = str(uuid.uuid4())
    start = datetime.now(UTC)

    async def scenario():
        await running_low(acme, f"sub_{uuid.uuid4().hex[:12]}")
        at, waited, paused = start, [], []

        for wait in (*AUTO_TOP_UP_RETRY_WAITS, None):
            assert await rows.claim_charge(COMPANY, acme, at) is not None
            paused.append(await charges.declined(COMPANY, acme, at))

            if wait is None:
                break

            # Not before its wait is over, and then once.
            early = await rows.claim_charge(COMPANY, acme, at + wait - timedelta(minutes=1))
            waited.append(early is None)
            at += wait

        later = await rows.claim_charge(COMPANY, acme, at + 60 * DAY)

        return waited, paused, later, await rows.get(COMPANY, acme)

    waited, paused, later, row = run(scenario())

    assert waited == [True, True, True]
    assert paused == [False, False, False, True]
    assert later is None
    assert row.declines == len(AUTO_TOP_UP_RETRY_WAITS) + 1


def test_a_hard_decline_pauses_at_once_and_saving_the_setting_doesnt_retry_it(run, paddle_calls):
    acme = str(uuid.uuid4())
    sub = f"sub_declined_hard_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await running_low(acme, sub)
        await auto_top_ups.check(COMPANY, acme)
        row = await rows.get(COMPANY, acme)
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, row.buyer_id, Currency.USD)
        later = await rows.claim_charge(COMPANY, acme, datetime.now(UTC) + 60 * DAY)

        return row, later, await auto_top_ups.out(COMPANY, acme, Currency.USD)

    row, later, shown = run(scenario())

    assert [call[0] for call in paddle_calls] == ["charge"]
    assert (row.declines, row.paused_at is not None) == (1, True)
    assert later is None
    assert shown.paused


def test_a_card_saved_after_the_pause_resumes_it_once(run, paddle_calls):
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"
    paused_at = datetime.now(UTC) - DAY

    async def scenario():
        await running_low(acme, sub)
        await charges.declined(COMPANY, acme, paused_at)
        await charges.pause(COMPANY, acme, paused_at)
        # A card saved before the pause (a late or replayed web hook) changes nothing.
        before = await charges.resume(sub, paused_at - timedelta(minutes=1))
        after = await charges.resume(sub, paused_at + timedelta(minutes=1))
        again = await charges.resume(sub, paused_at + timedelta(minutes=2))

        return before, after, again, await rows.get(COMPANY, acme)

    before, after, again, row = run(scenario())

    assert before is None
    assert after == (COMPANY, acme)
    assert again is None
    assert (row.paused_at, row.declines, row.retry_at) == (None, 0, None)


def test_a_charge_that_goes_through_starts_the_declines_over(run, paddle_calls):
    acme = str(uuid.uuid4())

    async def scenario():
        await running_low(acme, f"sub_{uuid.uuid4().hex[:12]}")
        # Declined ten days ago: its retry is due.
        await charges.declined(COMPANY, acme, datetime.now(UTC) - 10 * DAY)
        await auto_top_ups.check(COMPANY, acme)

        return await rows.get(COMPANY, acme)

    row = run(scenario())

    assert [call[0] for call in paddle_calls] == ["charge"]
    assert (row.declines, row.retry_at) == (0, None)
