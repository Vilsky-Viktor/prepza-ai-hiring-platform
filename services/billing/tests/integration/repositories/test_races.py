"""Billing's races against Postgres, each proven: the first call's transaction stays open at its
commit until the second is seen waiting on its lock (prepza_common.db.lock_waits), so the two really
overlap. Spending credits, charging a hold, a Paddle top-up and the automatic top-up. The held
transaction is the one its service opens (holds, topups) or, for a repository's own guarded
write, the one tests/integration/transactions.py opens for it."""

import os
import uuid
from datetime import UTC, datetime

from prepza_common.db.lock_waits import hold_first_commit, race

from billing.constants.credits import CANDIDATE_CREDITS, WELCOME_COMPANY, Reason
from billing.constants.products import TOP_UPS, OwnerType
from billing.repositories import auto_top_ups, ledger
from billing.services import holds, topups
from tests.integration import transactions
from tests.integration.factories import welcomed
from tests.integration.services.test_auto_top_up_retries import running_low

COMPANY = OwnerType.COMPANY
NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)


def test_two_holds_at_once_cant_both_take_the_last_credits(run, monkeypatch):
    acme = str(uuid.uuid4())

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        held = hold_first_commit(monkeypatch, transactions)
        reserve = (ledger.reserve, COMPANY, acme, WELCOME_COMPANY)
        results = await race(
            os.environ["DATABASE_URL"],
            held,
            transactions.transaction(*reserve, "candidate:a", Reason.CANDIDATE),
            transactions.transaction(*reserve, "candidate:b", Reason.CANDIDATE),
        )

        return results, await transactions.transaction(ledger.wallet, COMPANY, acme)

    results, wallet = run(scenario())

    assert results == (True, False)
    assert (wallet.balance, wallet.reserved) == (WELCOME_COMPANY, WELCOME_COMPANY)


def test_a_hold_charged_twice_at_once_takes_its_credits_once(run, monkeypatch):
    acme = str(uuid.uuid4())
    key = f"candidate:{acme}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await holds.hold(acme, acme)
        held = hold_first_commit(monkeypatch, holds)
        await race(os.environ["DATABASE_URL"], held, holds.charge(acme), holds.charge(acme))

        wallet = await transactions.transaction(ledger.wallet, COMPANY, acme)

        return wallet, await transactions.transaction(ledger.hold_status, key)

    wallet, status = run(scenario())

    assert (wallet.balance, wallet.reserved) == (WELCOME_COMPANY - CANDIDATE_CREDITS, 0)
    assert status == "charged"


def test_a_top_up_paddle_sends_twice_at_once_is_granted_once(run, monkeypatch):
    acme = str(uuid.uuid4())
    top_up = TOP_UPS[0]

    def grant():
        return topups.grant(
            COMPANY, acme, 1_000, 1, f"txn_{acme}", top_up.key, "ann", "1000", "USD", NOW
        )

    async def scenario():
        held = hold_first_commit(monkeypatch, topups)
        results = await race(os.environ["DATABASE_URL"], held, grant(), grant())
        wallet = await transactions.transaction(ledger.wallet, COMPANY, acme)

        return results, wallet.balance

    assert run(scenario()) == ((True, False), 1_000)


def test_two_checks_at_once_charge_the_automatic_top_up_once(run, monkeypatch, paddle_calls):
    acme = str(uuid.uuid4())

    async def scenario():
        await running_low(acme, f"sub_{uuid.uuid4().hex[:12]}")
        held = hold_first_commit(monkeypatch, transactions)
        claim = (auto_top_ups.claim_charge, COMPANY, acme, datetime.now(UTC))

        return await race(
            os.environ["DATABASE_URL"],
            held,
            transactions.transaction(*claim),
            transactions.transaction(*claim),
        )

    first, second = run(scenario())

    assert first is not None
    assert second is None
