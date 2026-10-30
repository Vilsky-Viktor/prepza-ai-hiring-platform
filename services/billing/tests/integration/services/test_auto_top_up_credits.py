import uuid
from datetime import UTC, datetime

from billing.constants.credits import WELCOME_COMPANY, Reason
from billing.constants.currencies import Currency
from billing.constants.products import AUTO_TOP_UP_COOLDOWN, OwnerType
from billing.repositories import auto_top_ups as rows
from billing.repositories import ledger
from billing.schemas.billing import AutoTopUpIn
from billing.services import auto_top_ups
from billing.services.topups import handle_completed
from tests.integration.conftest import charged
from tests.integration.factories import welcomed
from tests.integration.services.test_auto_top_ups import checkout_data
from tests.integration.transactions import transaction

COMPANY = OwnerType.COMPANY


def test_once_a_charges_credits_come_the_next_charge_waits_only_the_cooldown(run, paddle_calls):
    ann = f"user-{uuid.uuid4()}"
    acme = str(uuid.uuid4())
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await auto_top_ups.turn_on(
            COMPANY,
            acme,
            AutoTopUpIn(product="topup_50", threshold=500, agreed=True),
            ann,
            Currency.USD,
        )
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        await transaction(
            ledger.reserve,
            COMPANY,
            acme,
            WELCOME_COMPANY - 1,
            f"candidate:{uuid.uuid4()}",
            Reason.CANDIDATE,
        )
        await auto_top_ups.check(COMPANY, acme)
        # The charge's transaction.completed adds its credits, and they're used up again.
        await handle_completed(charged(sub))
        wallet = await transaction(ledger.wallet, COMPANY, acme)
        await transaction(
            ledger.reserve,
            COMPANY,
            acme,
            wallet.balance - wallet.reserved - 1,
            f"candidate:{uuid.uuid4()}",
            Reason.CANDIDATE,
        )

        return await transaction(
            rows.claim_charge, COMPANY, acme, datetime.now(UTC) + AUTO_TOP_UP_COOLDOWN * 2
        )

    assert run(scenario()) is not None
