from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.config.constants import VIA_MCP

from companies.constants.ai_apps import AI_APPS_OFF, KEY_OTHER_COMPANY
from companies.constants.invites import (
    COMPANY_SUSPENDED,
    INTERVIEW_UNAVAILABLE,
    INVITE_EXPIRED,
    NO_PLEDGE,
    InviteStatus,
)
from companies.constants.roles import EDITORS, Role
from companies.core.security import REQUEST_COMPANY, REQUEST_VIA
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies
from companies.repositories import invites as invite_store


async def require_company(user: CurrentUser, company_id: UUID) -> tuple[Company, Member]:
    """Any member: owners, admins and viewers. Enough for reading. An AI agent signed in with an
    API key reaches only the key's company (403)."""
    if key_refusal(company_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, KEY_OTHER_COMPANY)

    company = await companies.get(company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    member = member_of(company, user.uid)

    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    if refusal := ai_apps_refusal(company):
        raise HTTPException(status.HTTP_403_FORBIDDEN, refusal)

    return company, member


def key_refusal(company_id) -> str | None:
    """An AI agent signed in with an API key asking about another company than the key's."""
    key_company = REQUEST_COMPANY.get()

    if key_company is not None and key_company != str(company_id):
        return KEY_OTHER_COMPANY

    return None


def ai_apps_refusal(company: Company) -> str | None:
    """An AI app a member connected, while its owners and admins don't allow them."""
    if REQUEST_VIA.get() == VIA_MCP and company.ai_apps_off_at is not None:
        return AI_APPS_OFF

    return None


def suspension_refusal(company: Company) -> str | None:
    """Suspended by a superadmin: it can still be read (and deleted by its owner), not changed."""
    return COMPANY_SUSPENDED if company.suspended_at is not None else None


def member_of(company: Company, user_id: str) -> Member | None:
    return next((item for item in company.members if item.user_id == user_id), None)


def can_edit(member: Member) -> bool:
    return member.role in EDITORS


# Only the owner deletes the company and manages its members.
def is_owner(member: Member) -> bool:
    return member.role == Role.OWNER


async def require_editor(user: CurrentUser, company_id: UUID) -> tuple[Company, Member]:
    """An owner or admin: everything that changes the company or spends its credits."""
    company, member = await require_company(user, company_id)

    if not can_edit(member):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Viewers can't change anything here")

    if refusal := suspension_refusal(company):
        raise HTTPException(status.HTTP_403_FORBIDDEN, refusal)

    return company, member


def refuse_if_suspended(company: Company | None, invite_status: str | None) -> None:
    """For a candidate: a suspended company's interview isn't available (410), unless they're
    already in it, which they may finish."""
    suspended = company is not None and company.suspended_at is not None

    if suspended and invite_status != InviteStatus.IN_PROCESS:
        raise HTTPException(status.HTTP_410_GONE, INTERVIEW_UNAVAILABLE)


def refuse_without_pledge(pledged: bool, invite_status: str | None) -> None:
    """Starting takes the candidate's pledge to answer on their own (422); one already in the
    interview gave it and continues without."""
    if not pledged and invite_status != InviteStatus.IN_PROCESS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NO_PLEDGE)


async def open_invite(token: str) -> tuple[CandidateInvite, Interview]:
    """The invite a candidate's link names, with its interview: not found (404) when there's
    none, and gone (410, saying the company can send it again) once it expired."""
    found = await invite_store.get_by_token(token)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    if found[0].status == InviteStatus.EXPIRED:
        raise HTTPException(status.HTTP_410_GONE, INVITE_EXPIRED)

    return found
