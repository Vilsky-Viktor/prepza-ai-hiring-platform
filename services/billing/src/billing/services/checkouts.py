from fastapi import HTTPException, status

from billing.config import settings
from billing.constants.products import CANDIDATES_OUT_OF_RANGE, TOP_UP_UNAVAILABLE, OwnerType
from billing.helpers.credits import custom_top_up
from billing.integrations import paddle
from billing.schemas.billing import TopUpCheckoutOut
from billing.services.catalog import candidates_price
from billing.services.currencies import decide


async def company_checkout(
    company_id: str, candidates: int, buyer_id: str, country: str | None, language: str
) -> TopUpCheckoutOut:
    """A checkout for a top-up of `candidates`, paid into the company by `buyer_id`. What it buys
    and its price are set here from the count, in the company's currency, which Paddle then
    charges wherever the buyer is; its item is named in the buyer's `language`. A count outside
    the range, or before Paddle's product is set, is refused (422)."""
    currency = await decide(country, company_id=company_id)
    bought = custom_top_up(candidates, currency)

    if bought is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, CANDIDATES_OUT_OF_RANGE)

    if not settings.paddle_product_candidates:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, TOP_UP_UNAVAILABLE)

    count, cents = bought
    custom = {"owner_type": OwnerType.COMPANY, "owner_id": company_id, "buyer_id": buyer_id}
    item = {"price": candidates_price(count, cents, currency, None, language), "quantity": 1}

    return TopUpCheckoutOut(
        transaction_id=await paddle.create_transaction([item], currency, custom)
    )
