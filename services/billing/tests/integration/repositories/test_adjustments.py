"""A superadmin's adjustment of a company's credits, against the real database."""

import uuid

from billing.constants.credits import CANDIDATE_CREDITS, WELCOME_COMPANY, Reason
from billing.constants.products import OwnerType
from billing.repositories import history, ledger

COMPANY = OwnerType.COMPANY


def test_an_adjustment_moves_the_balance_once_and_keeps_its_note(run):
    acme = str(uuid.uuid4())
    key = f"adjustment:{uuid.uuid4()}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        added = await ledger.adjust(COMPANY, acme, 500, key, "Complaint 12: charged twice")
        again = await ledger.adjust(COMPANY, acme, 500, key, "Complaint 12: charged twice")
        wallet = await ledger.wallet(COMPANY, acme)

        return added, again, wallet.balance, await history.page(COMPANY, acme, 0, 1)

    added, again, balance, [newest] = run(scenario())

    assert (added, again) == (True, True)
    # Repeated with the same key, it counts once.
    assert balance == WELCOME_COMPANY + 500
    assert (newest.reason, newest.amount, newest.note) == (
        Reason.ADJUSTMENT,
        500,
        "Complaint 12: charged twice",
    )


def test_an_adjustment_never_takes_the_available_balance_below_zero(run):
    """Credits set aside for a candidate aren't available: removing them is refused."""
    acme = str(uuid.uuid4())

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, f"candidate:{acme}", "candidate")
        available = WELCOME_COMPANY - CANDIDATE_CREDITS
        too_much = await ledger.adjust(
            COMPANY, acme, -(available + 1), f"adjustment:{uuid.uuid4()}", "Too much"
        )
        all_of_it = await ledger.adjust(
            COMPANY, acme, -available, f"adjustment:{uuid.uuid4()}", "All of it"
        )

        return too_much, all_of_it, await ledger.wallet(COMPANY, acme)

    too_much, all_of_it, wallet = run(scenario())

    assert (too_much, all_of_it) == (False, True)
    assert (wallet.balance, wallet.reserved) == (CANDIDATE_CREDITS, CANDIDATE_CREDITS)
