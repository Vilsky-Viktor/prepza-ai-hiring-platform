import asyncio
import logging

import httpx
from fastapi import status

from billing.constants.payment_failures import (
    FAILURE_READ_TIMEOUT_SECONDS,
    FAILURE_READ_WAIT_SECONDS,
    FAILURE_READS,
    PaymentFailure,
)
from billing.helpers.payment_failures import latest_failure, paid_by
from billing.integrations import paddle

logger = logging.getLogger(__name__)


def told(transaction_id: str, reason: PaymentFailure, reads: int, why: str) -> PaymentFailure:
    """`reason`, logged with the transaction, how many reads it took and why (no buyer data)."""
    logger.info("Payment failure of %s: %s after %d reads (%s)", transaction_id, reason, reads, why)

    return reason


async def failure(
    owner_type: str, owner_id: str, buyer_id: str, transaction_id: str
) -> PaymentFailure | None:
    """Why the latest payment of this buyer's checkout into this wallet failed; None when the
    transaction isn't theirs (or Paddle has none by that id). Paddle failing or slow, or no code
    yet after the last read, is OTHER: the buyer still learns it failed and what to try."""
    for read in range(FAILURE_READS):
        if read:
            await asyncio.sleep(FAILURE_READ_WAIT_SECONDS)

        try:
            found = await paddle.transaction(transaction_id, FAILURE_READ_TIMEOUT_SECONDS)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == status.HTTP_404_NOT_FOUND:
                return None

            why = f"Paddle answered {error.response.status_code}"

            return told(transaction_id, PaymentFailure.OTHER, read + 1, why)
        except httpx.HTTPError as error:
            why = f"Paddle unreachable: {type(error).__name__}"

            return told(transaction_id, PaymentFailure.OTHER, read + 1, why)

        if not paid_by(found, owner_type, owner_id, buyer_id):
            return None

        reason = latest_failure(found)

        if reason is not None:
            code = found["payments"][0].get("error_code")

            return told(transaction_id, reason, read + 1, f"error code {code}")

    return told(transaction_id, PaymentFailure.OTHER, FAILURE_READS, "no error code yet")
