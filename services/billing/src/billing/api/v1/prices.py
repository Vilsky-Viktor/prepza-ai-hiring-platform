from fastapi import APIRouter, status

from billing.api.dependencies import Country, ServiceCaller
from billing.constants.currencies import ChoiceOwner
from billing.services.currencies import saved

# A new account's currency, for accounts' call on sign-up. `country` is the visitor's, which
# accounts passes on.
router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/currency", status_code=status.HTTP_204_NO_CONTENT)
async def remember_user_currency(
    user_id: str, caller: ServiceCaller, country: Country = None
) -> None:
    """On sign-up: the new account sees prices in its country's currency, until changed."""
    await saved(ChoiceOwner.USER, user_id, country)
