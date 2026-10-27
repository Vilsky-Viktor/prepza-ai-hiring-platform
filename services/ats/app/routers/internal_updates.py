from fastapi import APIRouter
from prepza_common.auth.service_auth import only_from
from prepza_common.config.constants import UPDATES_CALLER

from app.schemas.ats import NotInvitedIn, NotInvitedListOut
from app.service_auth import ServiceCaller
from app.services.not_invited import not_invited_between
from app.storage import not_invited

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/candidates/not-invited")
async def candidates_not_invited(body: NotInvitedIn, caller: ServiceCaller) -> NotInvitedListOut:
    """The assistant, for its get_updates tool: each candidate of these companies' ATSs who first
    couldn't be invited after `since` and up to `until`, and still isn't: the newest
    MAX_UPDATES, and how many in all."""
    only_from(caller, UPDATES_CALLER)
    window = (body.company_ids, body.since, body.until)

    return NotInvitedListOut(
        items=await not_invited_between(*window), total=await not_invited.count_between(*window)
    )
