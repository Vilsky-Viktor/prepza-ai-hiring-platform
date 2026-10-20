from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.constants.payment_failures import TRANSACTION_ID_PATTERN
from app.constants.products import OwnerType
from app.schemas.billing import PaymentFailureOut
from app.service_auth import ServiceCaller
from app.services import payment_failures

# Why a checkout's payment failed; companies checks that the user is one of its owners or admins.
router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/companies/{company_id}/payment-failure")
async def company_payment_failure(
    company_id: str,
    transaction_id: Annotated[str, Query(pattern=TRANSACTION_ID_PATTERN)],
    buyer_id: str,
    caller: ServiceCaller,
) -> PaymentFailureOut:
    """Why the latest payment of `buyer_id`'s checkout into the company failed; 404 for any
    transaction that isn't theirs, so its id alone reveals nothing."""
    reason = await payment_failures.failure(OwnerType.COMPANY, company_id, buyer_id, transaction_id)

    if reason is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return PaymentFailureOut(reason=reason)
