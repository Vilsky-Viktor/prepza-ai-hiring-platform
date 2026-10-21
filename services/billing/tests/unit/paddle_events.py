import hashlib
import hmac
import json
import time

SECRET = "pdl_ntfset_test_secret"


# The Paddle product billing sells every top-up under (tests/conftest.py).
PRODUCT = "pro_candidates"


def completed(
    owner_type="company",
    owner_id="acme",
    quantity=1,
    *,
    top_up="topup_50",
    candidates=None,
    currency="USD",
    subtotal="5000",
    product_id=PRODUCT,
):
    """Paddle's transaction.completed of a checkout billing made: one price made in the
    transaction under `product_id`, buying a fixed top-up (`top_up`) or `candidates`, paid
    `subtotal` before tax in `currency`."""
    bought = {"candidates": str(candidates)} if candidates is not None else {"top_up": top_up}

    return {
        "event_type": "transaction.completed",
        "data": {
            "id": "txn_01",
            # Billing created its checkout.
            "origin": "api",
            "currency_code": currency,
            "custom_data": {"owner_type": owner_type, "owner_id": owner_id, "buyer_id": "ann"},
            "items": [
                {
                    "price": {"id": "pri_made", "product_id": product_id, "custom_data": bought},
                    "quantity": quantity,
                }
            ],
            "details": {
                "totals": {"grand_total": "5000"},
                "line_items": [{"price_id": "pri_made", "totals": {"subtotal": subtotal}}],
            },
        },
    }


def adjustment(action="refund", status="approved", total="1000", adjustment_id="adj_01"):
    return {
        "event_type": "adjustment.updated",
        "data": {
            "id": adjustment_id,
            "action": action,
            "status": status,
            "transaction_id": "txn_01",
            "currency_code": "USD",
            "totals": {"total": total, "currency_code": "USD"},
        },
    }


def signed(event: dict, secret=SECRET, at=None) -> tuple[bytes, str]:
    """The body and Paddle-Signature header Paddle would send."""
    body = json.dumps(event).encode()
    timestamp = str(int(at if at is not None else time.time()))
    digest = hmac.new(secret.encode(), f"{timestamp}:".encode() + body, hashlib.sha256)

    return body, f"ts={timestamp};h1={digest.hexdigest()}"
