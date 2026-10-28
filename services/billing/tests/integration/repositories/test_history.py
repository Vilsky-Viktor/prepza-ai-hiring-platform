import uuid
from datetime import UTC, datetime

from billing.constants.credits import CANDIDATE_CREDITS, WELCOME_COMPANY, Reason
from billing.constants.products import TOP_UPS, OwnerType
from billing.repositories import history, ledger, purchases

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)
TOPUP = TOP_UPS[0]
COMPANY = OwnerType.COMPANY


def company():
    return str(uuid.uuid4())


def test_a_companys_history_is_newest_first_a_page_at_a_time(run):
    acme, other = company(), company()
    txn = f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.welcome_company(other, f"{other}@example.com")
        await purchases.grant(COMPANY, acme, 1_000, 1, txn, TOPUP.key, "ann", "1000", "USD", NOW)
        await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, f"candidate:{acme}", "candidate")
        await ledger.charge(f"candidate:{acme}")

        return (
            await history.page(COMPANY, acme, 0, 2),
            await history.page(COMPANY, acme, 2, 2),
        )

    first, second = run(scenario())

    assert [(row.reason, row.amount) for row in first + second] == [
        (Reason.CANDIDATE, -CANDIDATE_CREDITS),
        (Reason.TOPUP, 1_000),
        (Reason.WELCOME, WELCOME_COMPANY),
    ]
    assert {row.owner_id for row in first + second} == {acme}


def test_a_top_up_keeps_what_it_cost_and_whether_it_was_automatic(run):
    acme = company()
    by_hand, automatic = f"txn_{uuid.uuid4().hex}", f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await purchases.grant(
            COMPANY, acme, 1_000, 1, by_hand, TOPUP.key, "ann", "1000", "USD", NOW
        )
        await purchases.grant(
            COMPANY, acme, 3_000, 1, automatic, TOPUP.key, "ann", "3000", "EUR", NOW, True
        )

        return await history.page(COMPANY, acme, 0, 10)

    rows = {row.key.split(":")[0]: row for row in run(scenario())}

    assert (rows[by_hand].total_minor, rows[by_hand].currency, rows[by_hand].automatic) == (
        1000,
        "USD",
        False,
    )
    assert (rows[automatic].total_minor, rows[automatic].currency, rows[automatic].automatic) == (
        3000,
        "EUR",
        True,
    )


def test_a_refund_keeps_the_money_it_returned(run):
    acme = company()
    txn = f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await purchases.grant(COMPANY, acme, 1_000, 1, txn, TOPUP.key, "ann", "1000", "USD", NOW)
        await purchases.take_back(COMPANY, acme, -250, txn, "adj_01", Reason.REFUND, "250", "USD")

        return await history.page(COMPANY, acme, 0, 10)

    refund = next(row for row in run(scenario()) if row.reason == Reason.REFUND)

    assert (refund.amount, refund.total_minor, refund.currency, refund.automatic) == (
        -250,
        250,
        "USD",
        False,
    )


def test_only_the_company_that_bought_a_top_up_owns_it(run):
    acme, other = company(), company()
    txn = f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await purchases.grant(COMPANY, acme, 1_000, 1, txn, TOPUP.key, "ann", "1000", "USD", NOW)

        return (
            await purchases.owns(COMPANY, acme, txn),
            await purchases.owns(COMPANY, other, txn),
            await purchases.owns("user", acme, txn),
            await purchases.owns(COMPANY, acme, "txn_unknown"),
        )

    assert run(scenario()) == (True, False, False, False)


def test_a_company_has_paid_once_it_topped_up(run):
    acme, other = company(), company()

    async def scenario():
        txn = f"txn_{uuid.uuid4().hex}"
        await purchases.grant(COMPANY, acme, 1_000, 1, txn, TOPUP.key, "ann", "1000", "USD", NOW)

        return await purchases.paid(COMPANY, acme), await purchases.paid(COMPANY, other)

    assert run(scenario()) == (True, False)


def test_a_top_ups_transaction_finds_the_wallet_it_paid_into(run):
    acme = company()
    txn = f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await purchases.grant(COMPANY, acme, 1_000, 1, txn, TOPUP.key, "ann", "1000", "USD", NOW)

        return await purchases.for_transaction(txn), await purchases.for_transaction("txn_none")

    found, unknown = run(scenario())

    assert found[:2] == (COMPANY, acme)
    assert unknown is None
