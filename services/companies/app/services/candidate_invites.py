from fastapi import HTTPException, status
from prepza_common.analytics import track
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.names import clean_name
from prepza_common.rate_limit import hit_emails, recipient_key
from prepza_common.user import User

from app.constants.invites import (
    ALREADY_FINISHED,
    COMPANY_SUSPENDED,
    INTERVIEW_NOT_READY,
    NOT_STARTED,
    InviteStatus,
)
from app.helpers.candidates import new_hold_key
from app.helpers.interviews import interview_title
from app.helpers.logos import logo_path
from app.integrations import billing
from app.integrations.redis import get_redis
from app.models.companies import Company
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.services.candidate_billing import hold_again
from app.storage import audit, invites


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
        raise HTTPException(status.HTTP_409_CONFLICT, COMPANY_SUSPENDED)

    email = email.lower()

    current, stored = await invites.held(interview.id, email)
    key = stored if current else new_hold_key(interview.id)

    # Their results are in: inviting them again would only email them for nothing.
    if current == InviteStatus.FINISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_FINISHED)

    # A candidate who hasn't started has credits set aside: new, or sent again after expiring.
    # Credits first, so an invite refused for them never uses up the email limits.
    # Anything failing from setting the credits aside until the invite is saved (the email
    # limits, the title, the save, or billing's answer lost on the way) gives them back.
    try:
        if current is None or current in NOT_STARTED:
            await billing.hold_candidate(company.id, key)

        recipient = f"{interview.id}:{recipient_key(email)}"
        await hit_emails(get_redis(), user.uid, recipient, company.id)
        title = await interview_title(interview)

        # A ready interview has its title; without one, no email names it wrongly.
        if not title:
            raise HTTPException(status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY)

        invite, revived = await invites.upsert(
            interview.id,
            email,
            title,
            company.name,
            interview.language,
            logo_path(company),
            hold_key=key,
            name=clean_name(name),
            verified=company.verified_domain is not None,
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

    action = AuditAction.CANDIDATE_INVITED if current is None else AuditAction.INVITE_RESENT
    await audit.record(
        company.id, user.uid, action, invite.id, via=via, target_kind=TargetKind.CANDIDATE
    )

    return invite


async def give_back(interview: Interview, company: Company, email: str, current, key: str) -> None:
    """An invite that failed gives back the credits set aside for it just now: a new one's, or an
    expired one's (expiry had given them back). One already invited keeps its own. An expired
    invite sent again by another request meanwhile keeps them after all. Safe when nothing was
    set aside: billing releases only an open hold."""
    if current is not None and current != InviteStatus.EXPIRED:
        return

    await billing.release_candidate(key)

    if current == InviteStatus.EXPIRED and await invites.status_of(interview.id, email) not in (
        InviteStatus.EXPIRED,
        InviteStatus.DELETED,
    ):
        await billing.hold_candidate(company.id, key)
