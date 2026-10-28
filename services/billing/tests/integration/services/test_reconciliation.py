"""The daily reconciliation against the real database: a payment and a refund whose web hooks
never came are counted once, however often it runs, and what the web hooks did isn't redone."""

import uuid
from datetime import UTC, datetime

from billing.config import settings
from billing.constants.products import OwnerType
from billing.integrations import paddle
from billing.repositories import ledger
from billing.services.reconciliation import reconcile
from billing.services.topups import handle_completed
from tests.unit.paddle_events import PRODUCT, adjustment, completed

COMPANY = OwnerType.COMPANY
NOW = datetime.now(UTC)


def paid_into(company_id: str) -> dict:
    """A paid top-up of 10 candidates into the company, as Paddle's API lists it."""
    data = completed(owner_id=company_id)["data"]
    data["id"] = f"txn_{uuid.uuid4().hex}"

    return data


def refund_of(transaction: dict, total: str) -> dict:
    data = adjustment(total=total, adjustment_id=f"adj_{uuid.uuid4().hex}")["data"]
    data["transaction_id"] = transaction["id"]
    data["created_at"] = NOW.isoformat()

    return data


def paddle_lists(monkeypatch, transactions: list[dict], adjustments: list[dict]) -> None:
    """Paddle's lists as reconciliation reads them, and the product its top-ups are sold under."""

    async def completed_transactions(since):
        return transactions

    async def approved_adjustments(since):
        return adjustments

    monkeypatch.setattr(paddle, "completed_transactions", completed_transactions)
    monkeypatch.setattr(paddle, "approved_adjustments", approved_adjustments)
    monkeypatch.setattr(settings, "paddle_product_candidates", PRODUCT)


def test_a_payment_and_a_refund_the_web_hooks_missed_count_once(run, monkeypatch):
    acme = str(uuid.uuid4())
    transaction = paid_into(acme)
    # Half of the 5,000 cents paid comes back.
    paddle_lists(monkeypatch, [transaction], [refund_of(transaction, "2500")])

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        before = (await ledger.wallet(COMPANY, acme)).balance
        await reconcile(NOW)
        once = (await ledger.wallet(COMPANY, acme)).balance
        await reconcile(NOW)
        twice = (await ledger.wallet(COMPANY, acme)).balance

        return once - before, twice - before

    once, twice = run(scenario())

    # 10 candidates of 500 credits bought, half of them taken back.
    assert once == twice == 2500


def test_a_payment_its_web_hook_credited_isnt_credited_again(run, monkeypatch):
    acme = str(uuid.uuid4())
    transaction = paid_into(acme)
    paddle_lists(monkeypatch, [transaction], [])

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await handle_completed(transaction)
        before = (await ledger.wallet(COMPANY, acme)).balance
        await reconcile(NOW)

        return (await ledger.wallet(COMPANY, acme)).balance - before

    assert run(scenario()) == 0
