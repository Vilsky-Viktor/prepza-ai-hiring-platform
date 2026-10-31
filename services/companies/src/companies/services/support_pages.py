"""The admin zone's support pages of an account, a candidate and an interview: metadata only,
never a candidate's questions or answers."""

import logging

from fastapi import HTTPException, status
from testee_common.config.constants import MAX_PAGE_SIZE

from companies.constants.superadmin import CREDIT_STATES
from companies.core.db import Session
from companies.helpers.candidates import candidate_out
from companies.integrations import accounts, billing, rounds
from companies.repositories import candidates, companies, members, superadmin_support
from companies.schemas.superadmin_support import (
    SupportCandidateOut,
    SupportCandidateRowOut,
    SupportCompanyOut,
    SupportInterviewOut,
    SupportMemberOut,
    SupportSignalsOut,
    SupportTopUpOut,
    SupportUserCompanyOut,
    SupportUserOut,
)
from companies.services import candidate_results, set_cache
from companies.services.interview_views import interview_out

logger = logging.getLogger(__name__)
# Every company an account is a member of: a handful at most.
USER_COMPANIES = 1000


async def user_page(user_id: str) -> SupportUserOut | None:
    """None when there's neither an account nor a membership with that id."""
    account = await accounts.account(user_id)

    async with Session() as session:
        memberships = await superadmin_support.companies_of_user(session, user_id, USER_COMPANIES)

    if account is None and not memberships:
        return None

    bought = await billing.buyer_purchases(user_id)

    async with Session() as session:
        names = await companies.names(session, [row["company_id"] for row in bought])

    return SupportUserOut(
        user_id=user_id,
        email=account["email"] if account else None,
        created_at=account["created_at"] if account else None,
        companies=[
            SupportUserCompanyOut(id=company.id, name=company.name, role=role)
            for company, role in memberships
        ],
        top_ups=[
            SupportTopUpOut(**row, company_name=names.get(row["company_id"])) for row in bought
        ],
    )


async def candidate_page(invite, interview, company) -> SupportCandidateOut:
    """The candidate as their company's list shows them (results stored as there), with
    whether billing holds or charged their credits."""
    totals = (await rounds.invite_scores([invite.id])).get(str(invite.id)) or {}
    await candidate_results.sync([invite], {str(invite.id): totals})
    row = candidate_out(invite, totals, interview)
    hold = await billing.candidate_hold(invite.hold_key)

    return SupportCandidateOut(
        invite_id=invite.id,
        email=row.email,
        name=row.name,
        status=row.status,
        company_id=company.id,
        company_name=company.name,
        interview_id=interview.id,
        interview_title=interview.title,
        invited_at=row.created_at,
        last_sent_at=invite.sent_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        grade=row.grade,
        passed=row.passed,
        extra_time=row.extra_time,
        signals=SupportSignalsOut(
            tab_leaves=row.tab_leaves, copies=row.copies, fast_answers=row.fast_answers
        ),
        credits=CREDIT_STATES.get(hold),
    )


async def interview_page(interview, company) -> SupportInterviewOut:
    async with Session() as session:
        count = (await candidates.counts(session, [interview.id])).get(interview.id, 0)

    base = await interview_out(interview, count)
    found = await set_cache.get_set(interview.set_id) if interview.set_id else None

    return SupportInterviewOut(
        id=base.id,
        title=base.title,
        status=base.status,
        company_id=company.id,
        company_name=company.name,
        created_at=base.created_at,
        generation_id=base.generation_id,
        generation_failed=base.generation_failed,
        topics=[topic["title"] for topic in (found or {}).get("topics", [])],
        question_seconds=base.question_seconds,
        pass_mark=base.pass_mark,
        candidate_count=count,
    )


async def interview_candidates(interview, offset: int, limit: int) -> list[SupportCandidateRowOut]:
    """A page of the interview's candidates, newest first, as its company's list shows them."""
    rows = await candidate_results.page(interview, offset, limit, by_grade=False)

    return [
        SupportCandidateRowOut(
            invite_id=row.id,
            email=row.email,
            name=row.name,
            status=row.status,
            grade=row.grade,
            created_at=row.created_at,
        )
        for row in rows
    ]


async def company_page(company) -> SupportCompanyOut:
    """The company with its members and credits."""
    async with Session() as session:
        people = await members.list_for_company(session, company.id, 0, MAX_PAGE_SIZE)

    credits = await billing.company_credits(company.id)

    return SupportCompanyOut(
        id=company.id,
        name=company.name,
        verification_status=company.verification_status,
        verified_domain=company.verified_domain,
        suspended=company.suspended_at is not None,
        created_at=company.created_at,
        members=[
            SupportMemberOut(email=member.invited_email, role=member.role, user_id=member.user_id)
            for member in people
        ],
        balance=credits["balance"],
        reserved=credits["reserved"],
    )


async def adjust(company_id, amount: int, note: str, key: str, superadmin_id: str) -> None:
    """Adds or removes credits with a note the company's history shows; safe to repeat with the
    same key. Billing refuses taking the available balance below zero (409)."""
    async with Session() as session:
        company = await companies.get(session, company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    await billing.adjust_company(company_id, amount, note, key)
    logger.warning(
        "Credits of company %s adjusted by %d by superadmin %s", company_id, amount, superadmin_id
    )
