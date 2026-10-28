"""The admin zone's support pages of an account, a candidate and an interview: metadata only,
never a candidate's questions or answers."""

from companies.constants.superadmin import CREDIT_STATES
from companies.helpers.candidates import candidate_out
from companies.helpers.interviews import interview_out
from companies.integrations import billing, library, rounds
from companies.repositories import candidates, companies, superadmin_support
from companies.schemas.superadmin_support import (
    SupportCandidateOut,
    SupportCandidateRowOut,
    SupportInterviewOut,
    SupportSignalsOut,
    SupportTopUpOut,
    SupportUserCompanyOut,
    SupportUserOut,
)
from companies.services import candidate_results, set_cache

# Every company an account is a member of: a handful at most.
USER_COMPANIES = 1000


async def user_page(user_id: str) -> SupportUserOut | None:
    """None when there's neither an account nor a membership with that id."""
    account = await library.account(user_id)
    memberships = await superadmin_support.companies_of_user(user_id, USER_COMPANIES)

    if account is None and not memberships:
        return None

    bought = await billing.buyer_purchases(user_id)
    names = await companies.names([row["company_id"] for row in bought])

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
    count = (await candidates.counts([interview.id])).get(interview.id, 0)
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
