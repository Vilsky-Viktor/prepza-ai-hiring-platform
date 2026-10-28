from typing import Literal

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.db.paging import IdPageParams

from rounds.api.dependencies import ServiceCaller
from rounds.repositories import accounts, sessions
from rounds.schemas.sessions import InviteIdsIn, UserIdsOut

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, caller: ServiceCaller) -> None:
    """Part of deleting an account (library coordinates it); safe to repeat."""
    await accounts.delete_user(user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    return jsonable_encoder(await accounts.export(user_id))


@router.get("/users/ids")
async def user_ids(
    group: Literal["candidates", "learners"], caller: ServiceCaller, page: IdPageParams
) -> UserIdsOut:
    """Notifications, for a campaign to them, a page at a time: the candidates (people who took
    a company's interview) or the learners (people who took a free practice round). Only their
    ids: what they did stays here."""
    found = await accounts.user_ids(group == "learners", page.after, page.limit)

    return UserIdsOut(user_ids=found)


@router.post("/invites/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invite_sessions(body: InviteIdsIn, caller: ServiceCaller) -> None:
    """Companies' retention: candidates' sessions go with their expired invites."""
    await sessions.remove_for_invites(body.invite_ids)
