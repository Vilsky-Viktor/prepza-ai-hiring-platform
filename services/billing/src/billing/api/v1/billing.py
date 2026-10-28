import logging
import time

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.auth.auth import CurrentUser, OptionalUser
from prepza_common.config.constants import WEBHOOK_SIGNATURE_REFUSED

from billing.api.dependencies import Country
from billing.config import settings
from billing.constants.currencies import ChoiceOwner
from billing.constants.products import WEBHOOK_TOLERANCE_SECONDS
from billing.helpers.paddle import signature_valid
from billing.repositories import currencies
from billing.schemas.billing import CatalogOut, CurrencyIn, CurrencyOut
from billing.services.catalog import catalog_out
from billing.services.currencies import decide, saved
from billing.services.webhooks import handle

logger = logging.getLogger(__name__)
router = APIRouter(tags=["billing"])


@router.get("/catalog")
async def catalog(user: OptionalUser, country: Country = None) -> CatalogOut:
    """Every price: in the signed-in person's currency (their country's until they have one
    saved), or the signed-out visitor's country's."""
    return catalog_out(await decide(country, user.uid if user else None))


@router.get("/me/currency")
async def my_currency(user: CurrentUser, country: Country = None) -> CurrencyOut:
    return CurrencyOut(currency=await saved(ChoiceOwner.USER, user.uid, country))


@router.put("/me/currency")
async def choose_my_currency(body: CurrencyIn, user: CurrentUser) -> CurrencyOut:
    """Where prices outside a company's billing show in; travelling doesn't change it."""
    await currencies.choose(ChoiceOwner.USER, user.uid, body.currency)

    return CurrencyOut(currency=body.currency)


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
