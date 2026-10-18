from fastapi import APIRouter
from prepza_common.constants import UPDATES_CALLER
from prepza_common.service_auth import only_from

from app.schemas.ats import NotInvitedIn, NotInvitedListOut
from app.service_auth import ServiceCaller
from app.services.not_invited import not_invited_between

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/candidates/not-invited")
async def candidates_not_invited(body: NotInvitedIn, caller: ServiceCaller) -> NotInvitedListOut:
    """The assistant, for its get_updates tool: each candidate of these companies' ATSs who first
    couldn't be invited after `since` and up to `until`, and still isn't."""
    only_from(caller, UPDATES_CALLER)
    items = await not_invited_between(body.company_ids, body.since, body.until)

    return NotInvitedListOut(items=items)
