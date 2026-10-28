import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.auth.user import User
from prepza_common.db.paging import PageParams

from companies.core.db import Session
from companies.integrations import billing
from companies.models.companies import Company
from companies.repositories import companies, superadmin_support
from companies.schemas.audit import ActionOut
from companies.schemas.billing import CreditCandidateOut, HistoryEntryOut, InvoiceOut
from companies.schemas.interviews import InterviewOut
from companies.schemas.superadmin_support import (
    SupportAdjustmentIn,
    SupportCandidateOut,
    SupportCandidateRowOut,
    SupportCompanyOut,
    SupportInterviewOut,
    SupportSearchIn,
    SupportSearchOut,
    SupportUserOut,
)
from companies.services import (
    action_log,
    credit_history,
    interview_views,
    support_pages,
    support_search,
)

# The admin zone's support tab: superadmins look into a complaint about an account, a company's
# top-ups and spending, an interview or a candidate, and put a company's credits right. Each look
# and each adjustment goes to the logs with who did it and the ids they looked at, never an email
# address. A candidate's questions and answers are never shown.
router = APIRouter(prefix="/superadmin/support", tags=["superadmin"])
logger = logging.getLogger(__name__)


async def viewed(company_id: UUID, what: str, superadmin: User) -> Company:
    """The company, its view logged; 404 when it's gone."""
    async with Session() as session:
        company = await companies.get(session, company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    logger.info(
        "Support: %s of company %s viewed by superadmin %s", what, company_id, superadmin.uid
    )

    return company


async def viewed_interview(interview_id: UUID, what: str, superadmin: User) -> tuple:
    """The interview and its company, its view logged; 404 when it's gone."""
    async with Session() as session:
        found = await superadmin_support.interview(session, interview_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    logger.info(
        "Support: %s of interview %s of company %s viewed by superadmin %s",
        what,
        interview_id,
        found[1].id,
        superadmin.uid,
    )

    return found


@router.post("/search")
async def search(body: SupportSearchIn, superadmin: SuperadminUser) -> SupportSearchOut:
    """What a link, an id, a Paddle transaction, an email address or part of a company's name
    leads to, at most SUPPORT_RESULTS."""
    results = await support_search.search(body.query)
    logger.info(
        "Support: search by %s by superadmin %s found %s",
        support_search.kind_of(body.query),
        superadmin.uid,
        [result.id for result in results],
    )

    return SupportSearchOut(results=results)


@router.get("/companies/{company_id}")
async def get_company(company_id: UUID, superadmin: SuperadminUser) -> SupportCompanyOut:
    company = await viewed(company_id, "details", superadmin)

    return await support_pages.company_page(company)


@router.get("/companies/{company_id}/history")
async def get_history(
    company_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[HistoryEntryOut]:
    """Every movement of the company's credits, newest first, as its billing tab shows them."""
    await viewed(company_id, "credit history", superadmin)

    return await credit_history.page(company_id, page.offset, page.limit)


@router.get("/companies/{company_id}/reserved")
async def get_reserved(
    company_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[CreditCandidateOut]:
    await viewed(company_id, "reserved credits", superadmin)

    return await credit_history.reserved(company_id, page.offset, page.limit)


@router.get("/companies/{company_id}/interviews")
async def get_interviews(
    company_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[InterviewOut]:
    await viewed(company_id, "interviews", superadmin)

    return await interview_views.interviews_page(company_id, page.offset, page.limit)


@router.get("/companies/{company_id}/audit")
async def get_audit(
    company_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[ActionOut]:
    """The company's action log, newest first, as its owner sees it."""
    await viewed(company_id, "audit log", superadmin)

    return await action_log.page(company_id, page.offset, page.limit)


@router.get("/companies/{company_id}/invoice")
async def get_invoice(
    company_id: UUID, transaction_id: str, superadmin: SuperadminUser
) -> InvoiceOut:
    """A temporary link to the invoice of one of the company's top-ups."""
    await viewed(company_id, f"invoice {transaction_id}", superadmin)

    return InvoiceOut(url=await billing.company_invoice(company_id, transaction_id))


@router.post("/companies/{company_id}/adjustments", status_code=status.HTTP_204_NO_CONTENT)
async def adjust_credits(
    company_id: UUID, body: SupportAdjustmentIn, superadmin: SuperadminUser
) -> None:
    """Adds or removes credits with a note the company's history shows; safe to repeat with the
    same key. Billing refuses taking the available balance below zero (409)."""
    await support_pages.adjust(company_id, body.amount, body.note, body.key, superadmin.uid)


@router.get("/users/{user_id}")
async def get_user(user_id: str, superadmin: SuperadminUser) -> SupportUserOut:
    """The account with that id (as "copy id" gives it): its companies and the top-ups it paid
    for. 404 when there's neither an account nor a membership."""
    found = await support_pages.user_page(user_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    logger.info("Support: user %s viewed by superadmin %s", user_id, superadmin.uid)

    return found


@router.get("/candidates/{invite_id}")
async def get_candidate(invite_id: UUID, superadmin: SuperadminUser) -> SupportCandidateOut:
    async with Session() as session:
        found = await superadmin_support.candidate(session, invite_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    logger.info(
        "Support: candidate %s of company %s viewed by superadmin %s",
        invite_id,
        found[2].id,
        superadmin.uid,
    )

    return await support_pages.candidate_page(*found)


@router.get("/interviews/{interview_id}")
async def get_interview(interview_id: UUID, superadmin: SuperadminUser) -> SupportInterviewOut:
    interview, company = await viewed_interview(interview_id, "details", superadmin)

    return await support_pages.interview_page(interview, company)


@router.get("/interviews/{interview_id}/candidates")
async def get_interview_candidates(
    interview_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[SupportCandidateRowOut]:
    """The interview's candidates, newest first."""
    interview, _ = await viewed_interview(interview_id, "candidates", superadmin)

    return await support_pages.interview_candidates(interview, page.offset, page.limit)
