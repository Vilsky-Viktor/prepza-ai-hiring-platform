"""Starting a test through a job ad's link: who may start, the credits set aside for a new
candidate, their invite and the start itself (api/v1/links.py's start_link)."""

from fastapi import HTTPException, Request, status
from testee_common.auth.human_check import require_human
from testee_common.auth.user import User
from testee_common.events.analytics import track
from testee_common.http.client_ip import limit_address
from testee_common.limits.pause import refuse_if_paused
from testee_common.limits.rate_limit import hit

from companies.config import settings
from companies.constants.invites import (
    EMAIL_NOT_VERIFIED,
    INTERVIEW_NOT_READY,
    LINK_CLOSED,
    NOT_STARTED,
    InviteStatus,
)
from companies.core.db import Session
from companies.helpers.candidates import new_hold_key
from companies.helpers.logos import logo_path
from companies.integrations import billing
from companies.integrations.redis import get_redis
from companies.repositories import companies, invites, link_invites
from companies.schemas.invites import InviteStartOut
from companies.services import outbox as outbox_service
from companies.services.access import refuse_if_suspended, refuse_without_pledge
from companies.services.candidate_start import start_sessions
from companies.services.interview_views import attach_set, interview_title
from companies.services.invite_pages import linked_interview


async def joined_details(interview) -> dict:
    """What a new candidate's email with their own link says: the test and who it's for."""
    async with Session() as session:
        company = await companies.get(session, interview.company_id)

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

    async with Session() as session:
        company = await companies.get(session, interview.company_id)

    refuse_if_suspended(company, current)

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
        async with Session.begin() as session:
            invite = await link_invites.for_link(
                session, interview.id, user.email, hold_key=key, details=details
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


async def start_link(token: str, user: User, request: Request, pledged: bool) -> InviteStartOut:
    """The signed-in person becomes a candidate (their verified email, one attempt each) and
    starts, with credits set aside as for an email invite. A first start takes their pledge to
    answer on their own."""
    interview = await linked_interview(token)

    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, EMAIL_NOT_VERIFIED)

    # A link turned on before its questions were made holds nothing until they are.
    interview = await attach_set(interview)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY)

    async with Session() as session:
        current, stored = await invites.held(session, interview.id, user.email)

    refuse_without_pledge(pledged, current)
    key = stored if current else new_hold_key(interview.id)
    await admit(interview, user, current, request)
    # Credits set aside just now: a new candidate's, or an expired invite's (expiry gave them
    # back, and won't again). Anything failing before the candidate has started gives them back.
    fresh = current is None or current == InviteStatus.EXPIRED
    await hold_credits(interview, key, current, fresh)
    invite = await save_invite(interview, user, key, current, fresh)

    return await start(invite, interview, user, key, current)
