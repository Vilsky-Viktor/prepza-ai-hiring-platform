import asyncio
import os
import uuid
from datetime import UTC, datetime

from prepza_common.lock_waits import wait_for_lock_wait
from sqlalchemy import delete

from app.constants.credits import CANDIDATE_CREDITS, WELCOME_COMPANY, Reason
from app.constants.products import TOP_UPS, OwnerType
from app.models.billing import Hold, Wallet
from app.storage import ledger, purchases
from app.storage.db import Session
from app.storage.ledger import add

NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)
TOPUP = TOP_UPS[0]
TOPUP_CREDITS = 1_000
COMPANY = OwnerType.COMPANY


def company():
    return str(uuid.uuid4())


def test_a_candidate_is_charged_once_and_a_released_hold_comes_back(run):
    acme = company()

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        opened = await ledger.wallet(COMPANY, acme)
        held = await ledger.reserve(
            COMPANY, acme, CANDIDATE_CREDITS, "candidate:a", Reason.CANDIDATE
        )
        await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, "candidate:b", Reason.CANDIDATE)
        await ledger.charge("candidate:a")
        await ledger.charge("candidate:a")
        await ledger.release("candidate:b")

        return opened, held, await ledger.wallet(COMPANY, acme)

    opened, held, done = run(scenario())

    assert (opened.balance, opened.reserved) == (WELCOME_COMPANY, 0)
    assert held is True
    assert (done.balance, done.reserved) == (WELCOME_COMPANY - CANDIDATE_CREDITS, 0)


def test_credits_set_aside_cant_be_held_twice(run):
    acme = company()

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.reserve(COMPANY, acme, WELCOME_COMPANY, "candidate:all", Reason.CANDIDATE)

        return await ledger.reserve(COMPANY, acme, 1, "candidate:one-more", Reason.CANDIDATE)

    assert run(scenario()) is False


def test_a_retried_topup_is_granted_once(run):
    acme = company()

    async def scenario():
        args = (COMPANY, acme, TOPUP_CREDITS, 1, "txn", TOPUP.key, "ann", "1000")
        first = await purchases.grant(*args, "USD", NOW)
        again = await purchases.grant(*args, "USD", NOW)

        return first, again, (await ledger.wallet(COMPANY, acme)).balance

    assert run(scenario()) == (True, False, TOPUP_CREDITS)


def test_deleting_a_user_keeps_their_companys_purchases_without_them(run):
    acme, ann = company(), f"user-{uuid.uuid4()}"

    async def scenario():
        await purchases.grant(
            COMPANY, acme, TOPUP_CREDITS, 1, "txn2", TOPUP.key, ann, "1000", "USD", NOW
        )
        mine = await purchases.purchases_of(ann)
        await purchases.forget_buyer(ann)

        return mine, await purchases.purchases_of(ann), await purchases.for_transaction("txn2")

    mine, after, bought = run(scenario())

    assert [row.transaction_id for row in mine] == ["txn2"]
    assert after == []
    assert bought == (COMPANY, acme, TOPUP_CREDITS, 1000)


def test_a_new_company_by_the_same_person_doesnt_repeat_the_gift(run):
    email = f"user-{uuid.uuid4()}@Example.com"
    first, recreated = company(), company()

    async def scenario():
        assert await ledger.welcome_company(first, email)
        await purchases.delete_company(first)
        # The same Google account makes a new company.
        assert not await ledger.welcome_company(recreated, email.upper())

        return await ledger.wallet(COMPANY, recreated)

    assert run(scenario()).balance == 0


def test_a_refund_of_spent_credits_leaves_the_balance_negative(run):
    acme = company()

    async def scenario():
        await purchases.grant(
            COMPANY, acme, TOPUP_CREDITS, 1, "txn-r", TOPUP.key, "ann", "1000", "USD", NOW
        )
        await ledger.reserve(COMPANY, acme, 600, "candidate:spent", Reason.CANDIDATE)
        await ledger.charge("candidate:spent")
        await purchases.take_back(COMPANY, acme, -1_000, "txn-r", "r1", Reason.REFUND)
        # Paddle sends the same event again.
        await purchases.take_back(COMPANY, acme, -1_000, "txn-r", "r1", Reason.REFUND)
        blocked = await ledger.reserve(COMPANY, acme, 1, "candidate:after", Reason.CANDIDATE)

        return (await ledger.wallet(COMPANY, acme)).balance, blocked

    assert run(scenario()) == (-600, False)


def test_partial_refunds_add_up_and_one_counted_under_its_old_key_isnt_counted_again(run):
    acme = company()

    async def scenario():
        await purchases.grant(
            COMPANY, acme, TOPUP_CREDITS, 1, "txn_p%", TOPUP.key, "ann", "1000", "USD", NOW
        )
        first = await purchases.take_back(COMPANY, acme, -400, "txn_p%", "p1", Reason.REFUND)
        both = await purchases.take_back(COMPANY, acme, -600, "txn_p%", "p2", Reason.REFUND)
        # Taken back before keys carried the transaction; Paddle sends it again.
        async with Session() as session:
            await add(session, COMPANY, acme, -100, "adjustment:p0", Reason.REFUND)
            await session.commit()

        again = await purchases.take_back(COMPANY, acme, -100, "txn_p%", "p0", Reason.REFUND)
        # Another transaction's refund isn't this one's.
        other = await purchases.take_back(COMPANY, acme, -50, "txn_p", "q1", Reason.REFUND)

        return first, both, again, other, (await ledger.wallet(COMPANY, acme)).balance

    assert run(scenario()) == (400, 1_000, 1_000, 50, TOPUP_CREDITS - 1_150)


def test_charging_a_hold_while_its_company_is_deleted_doesnt_deadlock(run):
    acme = company()
    key = f"candidate:{acme}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, key, Reason.CANDIDATE)

        async with Session() as session:
            # As deleting the company does: the wallet goes first, then its holds.
            await session.execute(delete(Wallet).filter_by(owner_type=COMPANY, owner_id=acme))
            charging = asyncio.create_task(ledger.charge(key))
            # The charge waits on the wallet this transaction is deleting.
            await wait_for_lock_wait(os.environ["DATABASE_URL"])
            await session.execute(delete(Hold).filter_by(key=key))
            await session.commit()

        await charging

        return await ledger.wallets(COMPANY, [acme])

    assert run(scenario()) == {}
