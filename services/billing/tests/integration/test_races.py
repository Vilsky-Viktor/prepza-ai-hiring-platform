"""Billing's races against Postgres, each proven: the first call's transaction stays open at its
commit until the second is seen waiting on its lock (prepza_common.db.lock_waits), so the two really
overlap. Spending credits, charging a hold, a Paddle top-up and the automatic top-up."""

import os
import uuid
from datetime import UTC, datetime

from prepza_common.db.lock_waits import hold_first_commit, race

from app.constants.credits import CANDIDATE_CREDITS, WELCOME_COMPANY, Reason
from app.constants.products import TOP_UPS, OwnerType
from app.storage import auto_top_ups, ledger, purchases
from tests.integration.test_auto_top_up_retries import running_low

COMPANY = OwnerType.COMPANY
NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)


def test_two_holds_at_once_cant_both_take_the_last_credits(run, monkeypatch):
    acme = str(uuid.uuid4())

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        held = hold_first_commit(monkeypatch, ledger)
        results = await race(
            os.environ["DATABASE_URL"],
            held,
            ledger.reserve(COMPANY, acme, WELCOME_COMPANY, "candidate:a", Reason.CANDIDATE),
            ledger.reserve(COMPANY, acme, WELCOME_COMPANY, "candidate:b", Reason.CANDIDATE),
        )

        return results, await ledger.wallet(COMPANY, acme)

    results, wallet = run(scenario())

    assert results == (True, False)
    assert (wallet.balance, wallet.reserved) == (WELCOME_COMPANY, WELCOME_COMPANY)


def test_a_hold_charged_twice_at_once_takes_its_credits_once(run, monkeypatch):
    acme = str(uuid.uuid4())
    key = f"candidate:{acme}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, key, Reason.CANDIDATE)
        held = hold_first_commit(monkeypatch, ledger)
        await race(os.environ["DATABASE_URL"], held, ledger.charge(key), ledger.charge(key))

        return await ledger.wallet(COMPANY, acme), await ledger.hold_status(key)

    wallet, status = run(scenario())

    assert (wallet.balance, wallet.reserved) == (WELCOME_COMPANY - CANDIDATE_CREDITS, 0)
    assert status == "charged"


def test_a_top_up_paddle_sends_twice_at_once_is_granted_once(run, monkeypatch):
    acme = str(uuid.uuid4())
    top_up = TOP_UPS[0]

    def grant():
        return purchases.grant(
            COMPANY, acme, 1_000, 1, f"txn_{acme}", top_up.key, "ann", "1000", "USD", NOW
        )

    async def scenario():
        held = hold_first_commit(monkeypatch, purchases)
        results = await race(os.environ["DATABASE_URL"], held, grant(), grant())

        return results, (await ledger.wallet(COMPANY, acme)).balance

    assert run(scenario()) == ((True, False), 1_000)


def test_two_checks_at_once_charge_the_automatic_top_up_once(run, monkeypatch, paddle_calls):
    acme = str(uuid.uuid4())

    async def scenario():
        await running_low(acme, f"sub_{uuid.uuid4().hex[:12]}")
        held = hold_first_commit(monkeypatch, auto_top_ups)
        now = datetime.now(UTC)

        return await race(
            os.environ["DATABASE_URL"],
            held,
            auto_top_ups.claim_charge(COMPANY, acme, now),
            auto_top_ups.claim_charge(COMPANY, acme, now),
        )

    first, second = run(scenario())

    assert first is not None
    assert second is None
