from fastapi import APIRouter, HTTPException, status

from rounds.api.dependencies import ServiceCaller
from rounds.core.db import Session
from rounds.repositories import open_to_offers as open_to_offers_repo
from rounds.schemas.open_to_offers import MatchesIn, MatchOut, OpenProfileOut
from rounds.services import open_to_offers

# Companies, for an interview's Discover tab (companies checks the member and that the company
# has paid): who is open to offers with practice results on its topics.
router = APIRouter(prefix="/internal/open-to-offers", tags=["internal"])


@router.post("/matches")
async def matches(body: MatchesIn, caller: ServiceCaller) -> list[MatchOut]:
    """A page of the people open to offers with results on these template topics, whoever
    practised last first; topic ids in the body, as a list."""
    return await open_to_offers.matches(body.topic_ids, body.offset, body.limit)


@router.get("/{user_id}")
async def open_profile(user_id: str, caller: ServiceCaller) -> OpenProfileOut:
    """The person's shared profile while they're open to offers; 404 once they aren't, so an
    invite from an open tab can't reach someone who turned it off."""
    async with Session() as session:
        row = await open_to_offers_repo.get(session, user_id)

    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return OpenProfileOut(user_id=row.user_id, name=row.name, linkedin_url=row.linkedin_url)
