from prepza_common.events.notifications import NotificationKind, Recipient, notification

from app.constants.notifications import (
    CANDIDATE_LINK,
    INTERVIEW_LINK,
    INTERVIEWS_LINK,
    MEMBERS_LINK,
)
from app.constants.roles import EDITORS
from app.models.companies import Company, Member
from app.models.interviews import Interview


def interview_link(interview: Interview) -> str:
    return INTERVIEW_LINK.format(company_id=interview.company_id, interview_id=interview.id)


def candidate_finished(
    interview: Interview, invite_id: str, email: str, grade: int | None, name: str | None = None
) -> dict:
    """The grade and the candidate's name are left out while unknown. One per invite, though a
    retried event finishes the candidate again."""
    data = {
        "email": email,
        "title": interview.title,
        "candidate_link": CANDIDATE_LINK.format(
            company_id=interview.company_id, interview_id=interview.id, invite_id=invite_id
        ),
    }

    if grade is not None:
        data["grade"] = grade

    if name:
        data["candidate_name"] = name

    return notification(
        Recipient.COMPANY,
        interview.company_id,
        NotificationKind.CANDIDATE_FINISHED,
        interview_link(interview),
        key=str(invite_id),
        **data,
    )


def invite_undelivered(
    interview: Interview, invite_id: str, email: str, name: str | None = None
) -> dict:
    """With the candidate's name when it's known (the inviter's or the ATS's). Slack opens the
    candidate, where the invite is resent; the bell, the interview."""
    return notification(
        Recipient.COMPANY,
        interview.company_id,
        NotificationKind.INVITE_UNDELIVERED,
        interview_link(interview),
        email=email,
        title=interview.title,
        candidate_link=CANDIDATE_LINK.format(
            company_id=interview.company_id, interview_id=interview.id, invite_id=invite_id
        ),
        **({"candidate_name": name} if name else {}),
    )


def interview_ready(interview: Interview, title: str) -> dict:
    """One per interview, though a retried event saves its questions again."""
    return notification(
        Recipient.COMPANY,
        interview.company_id,
        NotificationKind.INTERVIEW_READY,
        interview_link(interview),
        key=str(interview.id),
        title=title,
    )


def interview_cancelled(interview: Interview) -> dict:
    """A cancelled interview never got its questions, so it rarely has a title."""
    data = {"title": interview.title} if interview.title else {}

    return notification(
        Recipient.COMPANY,
        interview.company_id,
        NotificationKind.INTERVIEW_CANCELLED,
        INTERVIEWS_LINK.format(company_id=interview.company_id),
        **data,
    )


def verification_decided(company: Company, approved: bool, reason: str | None) -> list[dict]:
    """One for each of the company's owners and admins (viewers can't act on it); a decline
    says why when the superadmin did."""
    kind = (
        NotificationKind.VERIFICATION_APPROVED
        if approved
        else NotificationKind.VERIFICATION_DECLINED
    )
    data = {"name": company.verification_name or company.name, "domain": company.website_domain}

    if reason:
        data["reason"] = reason

    return [
        notification(
            Recipient.USER,
            member.user_id,
            kind,
            INTERVIEWS_LINK.format(company_id=company.id),
            **data,
        )
        for member in company.members
        if member.user_id and member.role in EDITORS
    ]


def member_joined(company: Company, member: Member, owner_id: str) -> dict:
    """For the owner, who invited them: one per member, though accepting may be retried."""
    return notification(
        Recipient.USER,
        owner_id,
        NotificationKind.MEMBER_JOINED,
        MEMBERS_LINK.format(company_id=company.id),
        key=str(member.id),
        email=member.invited_email,
        name=company.name,
        role=member.role,
    )


def ownership_received(company: Company, member: Member, transfer_id: str) -> dict:
    """For the new owner, made so by the owner before them; once per transfer."""
    return notification(
        Recipient.USER,
        member.user_id,
        NotificationKind.OWNERSHIP_RECEIVED,
        MEMBERS_LINK.format(company_id=company.id),
        key=transfer_id,
        name=company.name,
    )
