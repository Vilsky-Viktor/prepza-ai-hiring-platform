from datetime import UTC, datetime

from fastapi import APIRouter, status
from testee_common.auth.auth import CurrentUser

from rounds.schemas.open_to_offers import OpenToOffersIn, OpenToOffersOut
from rounds.services import open_to_offers

# A practice user's own Open to offers switch: listed with their name, LinkedIn profile and
# practice results on the Discover tab of paying companies' matching interviews, until they turn
# it off, it lapses or they delete their account.
router = APIRouter(prefix="/open-to-offers", tags=["practice"])


@router.get("")
async def get_open_to_offers(user: CurrentUser) -> OpenToOffersOut:
    return await open_to_offers.current(user.uid)


@router.put("")
async def turn_on(body: OpenToOffersIn, user: CurrentUser) -> OpenToOffersOut:
    """Turns it on, or changes the profile, under the wording the person saw; each time is
    logged as their consent."""
    return await open_to_offers.turn_on(
        user.uid, user.name, body.linkedin_url, body.consent_version, datetime.now(UTC)
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def turn_off(user: CurrentUser) -> None:
    """Off every company's Discover tab at once."""
    await open_to_offers.turn_off(user.uid)
