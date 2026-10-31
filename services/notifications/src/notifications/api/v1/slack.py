from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse
from testee_common.auth.auth import CurrentUser

from notifications.integrations import companies
from notifications.schemas.slack import SlackKindsIn, SlackOut, SlackStartOut
from notifications.services import slack

router = APIRouter(prefix="/slack", tags=["slack"])


@router.get("")
async def get_slack(company_id: UUID, user: CurrentUser) -> SlackOut:
    """The company's Slack channel and the notifications it gets; every member sees it."""
    await companies.require(str(company_id), user.uid)

    return await slack.overview(str(company_id))


@router.get("/start")
async def start(company_id: UUID, user: CurrentUser) -> SlackStartOut:
    """Where "Add to Slack" goes: Slack's page to approve testee and pick a channel."""
    await companies.require(str(company_id), user.uid, editor=True)

    return SlackStartOut(url=await slack.start(str(company_id), user.uid))


@router.get("/callback")
async def callback(state: str, code: str | None = None, error: str | None = None):
    """Slack sends the browser back here; the signed, one-time state says whose company it is.
    Then on to the company's Slack page."""
    return RedirectResponse(await slack.finish(code, state, error), status.HTTP_303_SEE_OTHER)


@router.put("/kinds", status_code=status.HTTP_204_NO_CONTENT)
async def set_kinds(company_id: UUID, body: SlackKindsIn, user: CurrentUser) -> None:
    await companies.require(str(company_id), user.uid, editor=True)
    await slack.set_kinds(str(company_id), body.kinds, user.uid)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(company_id: UUID, user: CurrentUser) -> None:
    await companies.require(str(company_id), user.uid, editor=True)
    await slack.disconnect(str(company_id), user.uid)
