import logging
import time

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.constants import WEBHOOK_SIGNATURE_REFUSED

from app.config.settings import settings
from app.constants.credits import (
    CANDIDATE_CREDITS,
    REFERRAL_REWARD,
    WELCOME_COMPANY,
)
from app.constants.products import (
    CURRENCY,
    CUSTOM_TOP_UP_MAX,
    TOP_UPS,
    WEBHOOK_TOLERANCE_SECONDS,
)
from app.helpers.credits import candidate_prices, candidate_tiers, credits_for, upgrade_from
from app.helpers.paddle import signature_valid
from app.schemas.billing import (
    CandidatePriceOut,
    CandidateTierOut,
    CatalogOut,
    CustomTopUpOut,
    TopUpOut,
)
from app.services.catalog import price_ids
from app.services.webhooks import handle

logger = logging.getLogger(__name__)
router = APIRouter(tags=["billing"])


@router.get("/catalog")
def catalog() -> CatalogOut:
    prices = price_ids()
    custom_tiers = candidate_tiers()
    tiers = candidate_prices()
    cents = [price for _, price in tiers]

    return CatalogOut(
        environment=settings.paddle_environment,
        client_token=settings.paddle_client_token,
        currency=CURRENCY,
        candidate_credits=CANDIDATE_CREDITS,
        candidate_prices=[
            CandidatePriceOut(from_dollars=floor, cents=price) for floor, price in tiers
        ],
        candidate_cents_min=min(cents),
        candidate_cents_max=max(cents),
        welcome_company=WELCOME_COMPANY,
        free_candidates=WELCOME_COMPANY // CANDIDATE_CREDITS,
        referral_company=REFERRAL_REWARD,
        products=[
            TopUpOut(
                key=product.key,
                title=product.title,
                price_cents=product.price_cents,
                credits=credits_for(product.price_cents),
                candidates=credits_for(product.price_cents) // CANDIDATE_CREDITS,
                candidate_cents=product.price_cents
                * CANDIDATE_CREDITS
                // credits_for(product.price_cents),
                price_id=prices[product.key] or None,
            )
            for product in TOP_UPS
        ],
        custom=CustomTopUpOut(
            min_candidates=custom_tiers[0][0],
            max_candidates=CUSTOM_TOP_UP_MAX,
            on_sale=bool(settings.paddle_product_candidates),
            tiers=[
                CandidateTierOut(
                    from_candidates=count,
                    cents=cents,
                    upgrade_from=upgrade_from(index),
                )
                for index, (count, cents) in enumerate(custom_tiers)
            ],
        ),
    )


@router.post("/webhooks/paddle", status_code=status.HTTP_200_OK)
async def paddle_webhook(request: Request) -> dict:
    """Paddle retries until it gets a 2xx, and granting is idempotent, so retries are safe."""
    body = await request.body()
    signature = request.headers.get("Paddle-Signature", "")

    if not signature_valid(
        signature, body, settings.paddle_webhook_secret, time.time(), WEBHOOK_TOLERANCE_SECONDS
    ):
        logger.error("%s: paddle", WEBHOOK_SIGNATURE_REFUSED)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

    await handle(await request.json())

    return {"received": True}
