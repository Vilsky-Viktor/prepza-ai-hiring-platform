import uuid

from billing.config import settings
from billing.constants.products import OwnerType
from billing.repositories import ledger
from billing.services.adjustments import handle_adjustment
from billing.services.topups import handle_completed
from tests.integration.factories import welcomed
from tests.integration.transactions import transaction

COMPANY = OwnerType.COMPANY


def test_a_custom_top_up_grants_its_candidates_once_and_a_half_refund_takes_half(run, monkeypatch):
    monkeypatch.setattr(settings, "paddle_product_candidates", "pro_candidates")
    acme = str(uuid.uuid4())
    txn = {
        "id": f"txn_{uuid.uuid4().hex[:12]}",
        "origin": "api",
        "currency_code": "USD",
        "custom_data": {"owner_type": COMPANY, "owner_id": acme, "buyer_id": "ann"},
        "items": [
            {
                "price": {
                    "id": "pri_made_in_the_transaction",
                    "product_id": "pro_candidates",
                    "unit_price": {"amount": "20000", "currency_code": "USD"},
                    "custom_data": {"candidates": "50"},
                },
                "quantity": 1,
            }
        ],
        "details": {
            "totals": {"grand_total": "20000"},
            "line_items": [
                {"price_id": "pri_made_in_the_transaction", "totals": {"subtotal": "20000"}}
            ],
        },
    }

    async def balance():
        return (await transaction(ledger.wallet, COMPANY, acme)).balance

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        before = await balance()
        await handle_completed(txn)
        # Paddle retries the web hook.
        await handle_completed(txn)
        granted = await balance() - before
        await handle_adjustment(
            {
                "id": "adj_half",
                "action": "refund",
                "status": "approved",
                "transaction_id": txn["id"],
                "currency_code": "USD",
                "totals": {"total": "10000"},
            }
        )

        return granted, await balance() - before

    # 50 candidates at 500 credits; $100 of $200 back takes back half.
    assert run(scenario()) == (25_000, 12_500)
