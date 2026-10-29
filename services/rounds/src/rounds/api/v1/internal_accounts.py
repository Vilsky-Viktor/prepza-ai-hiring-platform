from typing import Literal

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.db.paging import IdPageParams

from rounds.api.dependencies import ServiceCaller
from rounds.core.db import Session
from rounds.repositories import accounts
from rounds.schemas.sessions import InviteIdsIn, UserIdsOut
from rounds.services import accounts as accounts_service
from rounds.services import session_removal

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    return jsonable_encoder(await accounts_service.export_user(user_id))


@router.get("/users/ids")
async def user_ids(
    group: Literal["candidates", "learners"], caller: ServiceCaller, page: IdPageParams
) -> UserIdsOut:
    """Notifications, for a campaign to them, a page at a time: the candidates (people who took
    a company's interview) or the learners (people who took a free practice round). Only their
    ids: what they did stays here."""
    async with Session() as session:
        found = await accounts.user_ids(session, group == "learners", page.after, page.limit)

    return UserIdsOut(user_ids=found)


@router.post("/invites/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invite_sessions(body: InviteIdsIn, caller: ServiceCaller) -> None:
    """Companies' retention: candidates' sessions go with their expired invites."""
    await session_removal.remove_invites(body.invite_ids)
