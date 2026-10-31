from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, status
from testee_common.auth.auth import CurrentUser
from testee_common.db.paging import PageParams

from companies.constants.discover import PERSON_ID_LENGTH
from companies.schemas.discover import DiscoverPersonOut
from companies.services import discover
from companies.services.interview_access import interview_for

# An interview's Discover tab: practice users who chose to be open to offers, with practice
# results on its subjects. Only companies that have topped up at least once (403 otherwise; the
# interview's `discover` says whether to show the tab).
router = APIRouter(prefix="/interviews/{interview_id}/discover", tags=["interviews"])


@router.get("")
async def list_people(
    interview_id: UUID, user: CurrentUser, page: PageParams
) -> list[DiscoverPersonOut]:
    """Every member reads it; whoever practised last first, never ranked."""
    interview, _, _ = await interview_for(user, interview_id)

    return await discover.people(interview, page.offset, page.limit)


@router.post("/{person_id}/invite", status_code=status.HTTP_204_NO_CONTENT)
async def invite_person(
    interview_id: UUID,
    person_id: Annotated[str, Path(max_length=PERSON_ID_LENGTH)],
    user: CurrentUser,
) -> None:
    """An owner or admin invites them to the interview, as any candidate."""
    interview, company, _ = await interview_for(user, interview_id, editor=True)
    await discover.invite(interview, company, user, person_id)
