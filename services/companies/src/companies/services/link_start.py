"""Starting a test through a job ad's link: who may start, the credits set aside for a new
candidate, their invite and the start itself (api/v1/links.py's start_link)."""

from fastapi import HTTPException, Request, status
from prepza_common.auth.human_check import require_human
from prepza_common.auth.user import User
from prepza_common.events.analytics import track
from prepza_common.http.client_ip import limit_address
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit

from companies.config import settings
from companies.constants.invites import LINK_CLOSED, NOT_STARTED, InviteStatus
from companies.helpers.interviews import interview_title
from companies.helpers.logos import logo_path
from companies.integrations import billing
from companies.integrations.redis import get_redis
from companies.repositories import companies, link_invites
from companies.schemas.invites import InviteStartOut
from companies.services import outbox as outbox_service
from companies.services.access import refuse_if_suspended
from companies.services.candidate_start import start_sessions


async def joined_details(interview) -> dict:
    """What a new candidate's email with their own link says: the test and who it's for."""
    company = await companies.get(interview.company_id)

    return {
        "title": await interview_title(interview) or "an interview",
        "company": company.name if company else "",
        "language": interview.language,
        "logo_path": logo_path(company),
    }


async def admit(interview, user: User, current: str | None, request: Request) -> None:
    """Refuses a finished candidate, a suspended company and, while paused, anyone not already
    in the interview. A new candidate shows they're a person and counts toward their address's
    and the link's hourly limits; one already invited is never held back by them. The address
    comes first, so one address refused can't go on using up the link's count for real
    candidates."""
    if current == InviteStatus.FINISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, "This interview is already finished")

    refuse_if_suspended(await companies.get(interview.company_id), current)

    # Paused, nobody starts; a candidate already in the interview may finish it.
    if current != InviteStatus.IN_PROCESS:
        await refuse_if_paused(get_redis(), "interview_start", interview.company_id, user.uid)

    if current is None:
        await require_human(request, settings.turnstile_secret_key)
        redis = get_redis()
        who = {"company_id": interview.company_id, "user_id": user.uid}
        address = limit_address(request)
        await hit(redis, f"rate:link-starts:ip:{address}", "LINK_STARTS_PER_IP_HOUR", **who)
        await hit(redis, f"rate:link-starts:{interview.id}", "LINK_STARTS_PER_HOUR", **who)


async def hold_credits(interview, key: str, current: str | None, fresh: bool) -> None:
    """Sets credits aside for a candidate who hasn't started; a company out of credits closes
    the link."""
    if current is not None and current not in NOT_STARTED:
        return

    try:
        await billing.hold_candidate(interview.company_id, key)
    except HTTPException as error:
        if error.status_code == status.HTTP_402_PAYMENT_REQUIRED:
            raise HTTPException(status.HTTP_409_CONFLICT, LINK_CLOSED) from error

        raise
    except Exception:
        # Billing's answer lost on the way: a hold made just now may exist. An invite's
        # earlier hold stays.
        if fresh:
            await billing.release_candidate(key)

        raise


async def save_invite(interview, user: User, key: str, current: str | None, fresh: bool):
    """The candidate's invite for the link, made or found."""
    try:
        details = await joined_details(interview) if current is None else None
        invite = await link_invites.for_link(
            interview.id, user.email, hold_key=key, details=details
        )
    except Exception:
        # An invite that couldn't be saved (its interview deleted meanwhile) gives its credits
        # back.
        if fresh:
            await billing.release_candidate(key)

        raise

    # Started at the same moment by another request, whose own key and credits were kept.
    if current is None and invite.hold_key != key:
        await billing.release_candidate(key)

    if current is None:
        await outbox_service.flush_quietly()
        await track("candidate_joined_by_link", company_id=interview.company_id)

    return invite


async def start(invite, interview, user: User, key: str, current: str | None) -> InviteStartOut:
    try:
        return await start_sessions(invite, interview, user)
    except Exception:
        # An expired invite that didn't start stays expired, and expiry won't give its credits
        # back: they go back now. A new one waits, unstarted, until it expires.
        if current == InviteStatus.EXPIRED:
            await billing.release_candidate(key)

        raise
