import asyncio

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

            return PaymentFailure.OTHER
        except httpx.HTTPError:
            return PaymentFailure.OTHER

        if not paid_by(found, owner_type, owner_id, buyer_id):
            return None

        reason = latest_failure(found)

        if reason is not None:
            return reason

    return PaymentFailure.OTHER
