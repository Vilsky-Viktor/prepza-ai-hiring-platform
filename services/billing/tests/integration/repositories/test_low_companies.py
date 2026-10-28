import uuid

from billing.constants.credits import CANDIDATE_CREDITS
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.models.billing import Wallet
from billing.repositories import auto_top_ups as rows
from billing.repositories import ledger

COMPANY = OwnerType.COMPANY


async def wallet(available: int) -> str:
    owner = str(uuid.uuid4())

    async with Session() as session:
        session.add(Wallet(owner_type=COMPANY, owner_id=owner, balance=available, reserved=0))
        await session.commit()

    return owner


def test_running_low_lists_companies_short_of_a_candidate_unless_a_top_up_refills_them(run):
    async def scenario():
        low = await wallet(CANDIDATE_CREDITS - 1)
        enough = await wallet(CANDIDATE_CREDITS)
        refilled = await wallet(0)
        await rows.save(COMPANY, refilled, "topup_50", 500, "ann", 5000, "USD")
        await rows.start(COMPANY, refilled, "ann", f"sub_{uuid.uuid4().hex[:12]}", "USD")
        found = {row.owner_id for row in await ledger.running_low(COMPANY)}

        return found & {low, enough, refilled}, low

    found, low = run(scenario())

    assert found == {low}


def test_running_low_with_owner_ids_lists_only_those_owners(run):
    async def scenario():
        asked = await wallet(0)
        asked_enough = await wallet(CANDIDATE_CREDITS)
        await wallet(0)
        found = await ledger.running_low(COMPANY, [asked, asked_enough])

        return [row.owner_id for row in found], asked

    found, asked = run(scenario())

    assert found == [asked]


def test_running_low_counts_an_automatic_top_up_waiting_for_its_checkout(run):
    async def scenario():
        waiting = await wallet(0)
        await rows.save(COMPANY, waiting, "topup_50", 500, "ann", 5000, "USD")
        found = await ledger.running_low(COMPANY, [waiting])

        return [row.owner_id for row in found], waiting

    found, waiting = run(scenario())

    assert found == [waiting]


def test_running_low_leaves_out_an_asked_owner_with_an_active_automatic_top_up(run):
    async def scenario():
        refilled = await wallet(0)
        await rows.save(COMPANY, refilled, "topup_50", 500, "ann", 5000, "USD")
        await rows.start(COMPANY, refilled, "ann", f"sub_{uuid.uuid4().hex[:12]}", "USD")

        return await ledger.running_low(COMPANY, [refilled])

    assert run(scenario()) == []


def test_running_low_takes_credits_set_aside_off_the_balance(run):
    async def scenario():
        owner = str(uuid.uuid4())

        async with Session() as session:
            session.add(
                Wallet(owner_type=COMPANY, owner_id=owner, balance=CANDIDATE_CREDITS, reserved=1)
            )
            await session.commit()

        found = await ledger.running_low(COMPANY, [owner])

        return [row.owner_id for row in found], owner

    found, owner = run(scenario())

    assert found == [owner]


def test_running_low_comes_a_page_at_a_time_by_company_id(run):
    async def scenario():
        owners = sorted([await wallet(0) for _ in range(3)])
        one = await ledger.running_low(COMPANY, None, owners[0], 1)
        rest = await ledger.running_low(COMPANY, None, owners[0], 5000)

        return owners, [row.owner_id for row in one], [row.owner_id for row in rest]

    owners, one, rest = run(scenario())

    # Other tests' wallets may come between: the page is in order, after the given id, bounded.
    assert len(one) == 1 and one[0] > owners[0]
    assert rest == sorted(rest) and {owners[1], owners[2]} <= set(rest)
