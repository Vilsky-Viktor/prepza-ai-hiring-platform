import asyncio
import uuid
from datetime import UTC, datetime

from app.constants.credits import REFERRAL_REWARD, WELCOME_COMPANY, WELCOME_GIFT
from app.constants.products import OwnerType
from app.helpers.gifts import legacy_gift_key
from app.models.billing import Gift
from app.services.adjustments import handle_adjustment
from app.services.referrals import reward_after_top_up
from app.storage import ledger, purchases, referrals
from app.storage.db import Session

COMPANY = OwnerType.COMPANY


def company():
    return str(uuid.uuid4())


async def available(owner_type, owner_id):
    row = await ledger.wallet(owner_type, owner_id)

    return row.balance - row.reserved


def test_a_referral_pays_both_companies_once_on_a_big_enough_top_up(run):
    acme, newco = company(), company()

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        code = await referrals.code_of(COMPANY, acme)
        same_code = await referrals.code_of(COMPANY, acme)
        await ledger.welcome_company(newco, f"{newco}@example.com")
        recorded = await referrals.record(code, COMPANY, newco, [])
        await reward_after_top_up(COMPANY, newco, "txn_1")
        await reward_after_top_up(COMPANY, newco, "txn_2")

        return (
            code == same_code,
            recorded,
            await available(COMPANY, acme),
            await available(COMPANY, newco),
            await referrals.rewarded_count(COMPANY, acme),
            [(row.owner_id, paid) for row, paid in await referrals.rewards(COMPANY, acme, 10)],
        )

    same, recorded, acme_credits, newco_credits, count, rewarded = run(scenario())

    assert same and recorded
    assert acme_credits == newco_credits == WELCOME_COMPANY + REFERRAL_REWARD
    assert count == 1
    assert rewarded == [(newco, REFERRAL_REWARD)]


def test_own_codes_related_companies_and_unknown_codes_refer_nobody(run):
    acme, sister, other = (company() for _ in range(3))

    async def scenario():
        acme_code = await referrals.code_of(COMPANY, acme)

        return (
            await referrals.record(acme_code, COMPANY, acme, []),
            await referrals.record(acme_code, COMPANY, sister, [acme]),
            await referrals.record("nope", COMPANY, other, []),
            await referrals.record(acme_code, COMPANY, other, []),
        )

    assert run(scenario()) == (False, False, False, True)


def test_a_deleted_referrer_leaves_the_new_company_its_own_reward(run):
    acme, newco = str(uuid.uuid4()), str(uuid.uuid4())

    async def scenario():
        await ledger.welcome_company(newco, f"{newco}@example.com")
        code = await referrals.code_of(OwnerType.COMPANY, acme)
        await referrals.record(code, OwnerType.COMPANY, newco, [])
        await purchases.delete_company(acme)
        await reward_after_top_up(OwnerType.COMPANY, newco, "txn_1")

        return (
            await available(OwnerType.COMPANY, newco),
            await ledger.wallets(OwnerType.COMPANY, [acme]),
        )

    credits, gone = run(scenario())

    assert credits == WELCOME_COMPANY + REFERRAL_REWARD
    assert gone == {}


def test_a_referrer_over_the_yearly_limit_is_neither_paid_nor_told(run, monkeypatch):
    acme, first, second = company(), company(), company()
    monkeypatch.setattr(referrals, "REFERRALS_PER_YEAR", 1)

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        code = await referrals.code_of(COMPANY, acme)
        paid = []

        for newco in (first, second):
            await ledger.welcome_company(newco, f"{newco}@example.com")
            await referrals.record(code, COMPANY, newco, [])
            paid.append(await referrals.reward(COMPANY, newco, f"txn_{newco}"))

        listed = [
            (row.owner_id, credits) for row, credits in await referrals.rewards(COMPANY, acme, 10)
        ]

        return paid, await available(COMPANY, acme), await available(COMPANY, second), listed

    paid, acme_credits, second_credits, listed = run(scenario())

    # The second is listed as it paid the referrer: nothing.
    assert sorted(listed) == sorted([(first, REFERRAL_REWARD), (second, 0)])

    assert paid == [acme, None]
    assert acme_credits == WELCOME_COMPANY + REFERRAL_REWARD
    assert second_credits == WELCOME_COMPANY + REFERRAL_REWARD


def test_two_rewards_at_once_dont_pass_the_referrers_yearly_limit(run, monkeypatch):
    acme, first, second = company(), company(), company()
    monkeypatch.setattr(referrals, "REFERRALS_PER_YEAR", 1)
    add = referrals.add

    async def slow_add(*args):
        # Both rewards reach the count before either is saved.
        await asyncio.sleep(0.3)

        return await add(*args)

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        code = await referrals.code_of(COMPANY, acme)

        for newco in (first, second):
            await ledger.welcome_company(newco, f"{newco}@example.com")
            await referrals.record(code, COMPANY, newco, [])

        monkeypatch.setattr(referrals, "add", slow_add)
        paid = await asyncio.gather(
            *(referrals.reward(COMPANY, newco, f"txn_{newco}") for newco in (first, second))
        )

        return paid, await available(COMPANY, acme)

    paid, acme_credits = run(scenario())

    assert sorted(paid, key=bool) == [None, acme]
    assert acme_credits == WELCOME_COMPANY + REFERRAL_REWARD


def refund(transaction_id, total):
    return {
        "id": f"adj_{uuid.uuid4().hex[:12]}",
        "action": "refund",
        "status": "approved",
        "transaction_id": transaction_id,
        "totals": {"total": total},
    }


def test_a_full_refund_of_the_rewarding_top_up_takes_both_rewards_back(run):
    acme, newco = company(), company()
    paid, refunded = f"txn_{uuid.uuid4().hex[:12]}", f"txn_{uuid.uuid4().hex[:12]}"

    async def top_up(transaction_id):
        await purchases.grant(
            COMPANY,
            newco,
            3_000,
            1,
            transaction_id,
            "topup_50",
            None,
            "3000",
            "USD",
            datetime.now(UTC),
        )
        await reward_after_top_up(COMPANY, newco, transaction_id)

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.welcome_company(newco, f"{newco}@example.com")
        await referrals.record(await referrals.code_of(COMPANY, acme), COMPANY, newco, [])
        await top_up(refunded)
        # A partial refund keeps the rewards; a full one, sent twice, takes them back once.
        await handle_adjustment(refund(refunded, "1000"))
        partly = await available(COMPANY, acme)
        full = refund(refunded, "3000")
        await handle_adjustment(full)
        await handle_adjustment(full)
        taken_back = (
            await available(COMPANY, acme),
            await referrals.rewarded_count(COMPANY, acme),
        )
        # Paddle sending the refunded top-up again pays nothing; the next real top-up pays.
        await reward_after_top_up(COMPANY, newco, refunded)
        replayed = await referrals.rewarded_count(COMPANY, acme)
        await top_up(paid)

        return partly, taken_back, replayed, await available(COMPANY, acme)

    partly, taken_back, replayed, again = run(scenario())

    assert partly == WELCOME_COMPANY + REFERRAL_REWARD
    assert taken_back == (WELCOME_COMPANY, 0)
    assert replayed == 0
    assert again == WELCOME_COMPANY + REFERRAL_REWARD


def test_an_owner_given_the_welcome_gift_under_the_old_key_isnt_given_it_again(run):
    first, second = company(), company()

    async def scenario():
        async with Session() as session:
            session.add(Gift(key=legacy_gift_key(WELCOME_GIFT, "Ann.Lee+jobs@gmail.com")))
            await session.commit()

        return await ledger.welcome_company(second, "ann.lee+jobs@gmail.com")

    assert run(scenario()) is False
    assert first != second


def test_a_welcome_asked_again_counts_once_and_still_records_the_referral(run):
    acme, newco = company(), company()

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        code = await referrals.code_of(COMPANY, acme)
        # The first answer was lost: companies asks again for the same company.
        first = await ledger.welcome_company(newco, f"{newco}@example.com")
        again = await ledger.welcome_company(newco, f"{newco}@example.com")
        recorded = again and await referrals.record(code, COMPANY, newco, [])

        return first, again, recorded, await available(COMPANY, newco)

    assert run(scenario()) == (True, True, True, WELCOME_COMPANY)


def test_deleting_the_referred_company_doesnt_keep_the_referrers_reward_from_a_refund(run):
    """Otherwise: top up, delete the company, have the top-up refunded, and the referrer keeps
    a reward nobody paid for, up to the yearly limit."""
    acme, newco = company(), company()
    paid = f"txn_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.welcome_company(newco, f"{newco}@example.com")
        await referrals.record(await referrals.code_of(COMPANY, acme), COMPANY, newco, [])
        await purchases.grant(
            COMPANY, newco, 3_000, 1, paid, "topup_50", None, "3000", "USD", datetime.now(UTC)
        )
        await reward_after_top_up(COMPANY, newco, paid)
        rewarded = await available(COMPANY, acme)
        await purchases.delete_company(newco)
        await handle_adjustment(refund(paid, "3000"))

        return rewarded, await available(COMPANY, acme)

    rewarded, after = run(scenario())

    assert rewarded == WELCOME_COMPANY + REFERRAL_REWARD
    assert after == WELCOME_COMPANY
