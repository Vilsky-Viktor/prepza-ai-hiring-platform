from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.events.analytics import track
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.i18n.i18n import CodedError
from prepza_common.i18n.names import clean_name
from prepza_common.limits.rate_limit import hit_emails, recipient_key

from companies.constants import error_codes
from companies.constants.audit import VIA_API
from companies.constants.invites import (
    ALREADY_FINISHED,
    COMPANY_SUSPENDED,
    INTERVIEW_NOT_READY,
    NO_EMAILS_FOR_GUEST,
    NOT_STARTED,
    InviteStatus,
)
from companies.core.db import Session
from companies.helpers.candidates import new_hold_key
from companies.helpers.logos import logo_path
from companies.integrations import billing
from companies.integrations.redis import get_redis
from companies.models.companies import Company
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import audit, companies, invites
from companies.services import outbox as outbox_service
from companies.services.candidate_billing import hold_again
from companies.services.interview_views import interview_title


async def invite(
    interview: Interview,
    company: Company,
    user: User,
    email: str,
    name: str | None = None,
    return_url: str | None = None,
    sign_in: bool = True,
    theme: str | None = None,
    via: str | None = None,
) -> CandidateInvite:
    """Invites one candidate, or sends their invite again, with the invite email queued; `name`
    (untrusted: cleaned here) fills their name if it isn't known yet. Raises 429 over the
    member's email limits and billing's 402 when the company is out of credits, and 409 while a
    superadmin has the company suspended (an ATS keeps its candidates waiting then). The action
    log records it as `user`'s, through `via` when an ATS or the API sent it."""
    if company.suspended_at is not None:
        raise CodedError(status.HTTP_409_CONFLICT, COMPANY_SUSPENDED, error_codes.COMPANY_SUSPENDED)

    email = email.lower()

    async with Session() as session:
        current, stored = await invites.held(session, interview.id, email)

    key = stored if current else new_hold_key(interview.id)

    # Their results are in: inviting them again would only email them for nothing.
    if current == InviteStatus.FINISHED:
        raise CodedError(status.HTTP_409_CONFLICT, ALREADY_FINISHED, error_codes.CANDIDATE_FINISHED)

    # A candidate who hasn't started has credits set aside: new, or sent again after expiring.
    # Credits first, so an invite refused for them never uses up the email limits.
    # Anything failing from setting the credits aside until the invite is saved (the email
    # limits, the title, the save, or billing's answer lost on the way) gives them back.
    try:
        if current is None or current in NOT_STARTED:
            await billing.hold_candidate(company.id, key)

        title = await interview_title(interview)

        # A ready interview has its title; without one, no email names it wrongly. Refused
        # before the email limits, which an email never sent mustn't use up.
        if not title:
            raise CodedError(
                status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY, error_codes.INTERVIEW_NOT_READY
            )

        recipient = f"{interview.id}:{recipient_key(email)}"
        await hit_emails(get_redis(), user.uid, recipient, company.id)

        action = AuditAction.CANDIDATE_INVITED if current is None else AuditAction.INVITE_RESENT
        invite, revived = await save(
            interview,
            company,
            email,
            title,
            (user.uid, action, via),
            hold_key=key,
            name=clean_name(name),
            return_url=return_url,
            sign_in=sign_in,
            theme=theme,
        )
    except Exception:
        await give_back(interview, company, email, current, key)

        raise

    # Invited at the same moment by another request, whose own key and credits were kept.
    if current is None and invite.hold_key != key:
        await billing.release_candidate(key)

    # Expired after it was read here: expiry gave its credits back.
    if revived:
        await hold_again(invite, key)

    if current is None:
        await track("candidate_invited", user_id=user.uid, company_id=company.id)

    return invite


async def save(
    interview: Interview, company: Company, email: str, title: str, audited: tuple, **options
) -> tuple[CandidateInvite, bool]:
    """The invite with its email queued (invites.upsert, with its `options`) and its line in the
    action log (`audited`: the user's id, the action and the way it came), in one save; whether
    it revived an expired invite."""
    user_id, action, via = audited

    async with Session.begin() as session:
        invite, revived = await invites.upsert(
            session,
            interview.id,
            email,
            title,
            company.name,
            interview.language,
            logo_path(company),
            verified=company.verified_domain is not None,
            **options,
        )
        await audit.record(
            session,
            company.id,
            user_id,
            action,
            invite.id,
            via=via,
            target_kind=TargetKind.CANDIDATE,
        )

    return invite, revived


async def give_back(interview: Interview, company: Company, email: str, current, key: str) -> None:
    """An invite that failed gives back the credits set aside for it just now: a new one's, or an
    expired one's (expiry had given them back). One already invited keeps its own. An expired
    invite sent again by another request meanwhile keeps them after all. Safe when nothing was
    set aside: billing releases only an open hold."""
    if current is not None and current != InviteStatus.EXPIRED:
        return

    await billing.release_candidate(key)

    if current != InviteStatus.EXPIRED:
        return

    async with Session() as session:
        now = await invites.status_of(session, interview.id, email)

    if now not in (InviteStatus.EXPIRED, InviteStatus.DELETED):
        await billing.hold_candidate(company.id, key)


async def resend(company_id, interview: Interview, found: CandidateInvite, user_id: str) -> None:
    """Sends the invite again, as an owner or admin does on the candidate's page, for the public
    API: refused for a candidate who finished (409) or one prepza doesn't email (invited without
    a sign-in, 409); the invite keeps its return address and theme."""
    if found.status == InviteStatus.DELETED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    if found.guest:
        raise CodedError(
            status.HTTP_409_CONFLICT, NO_EMAILS_FOR_GUEST, error_codes.INVITED_WITHOUT_SIGN_IN
        )

    async with Session() as session:
        company = await companies.get(session, company_id)

    sender = User(uid=user_id, email="", email_verified=True)
    await invite(interview, company, sender, found.email, via=VIA_API)
    await outbox_service.flush_quietly()
