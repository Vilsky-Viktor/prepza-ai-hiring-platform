from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.db.paging import PageParams

from companies.api.dependencies import ServiceCaller
from companies.constants.audit import VIA_API
from companies.core.db import Session
from companies.repositories import companies
from companies.schemas.interview_notes import NoteIn, NoteOut
from companies.services import interview_notes
from companies.services.access import trusted_member
from companies.services.interview_views import company_interview

# An interview's notes through an API key, as `user_id`, the key itself (key_actor; the api
# service checked it's the company's).
router = APIRouter(
    prefix="/internal/companies/{company_id}/interviews/{interview_id}/notes", tags=["internal"]
)


async def key_member(company_id: UUID, interview_id: UUID, user_id: str):
    """The interview, its company and the key acting in it; 404 when either is missing."""
    interview = await company_interview(company_id, interview_id)

    async with Session() as session:
        company = await companies.get(session, company_id)

    member = trusted_member(company, user_id) if company else None

    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    return interview, company, member


@router.get("")
async def list_notes(
    company_id: UUID, interview_id: UUID, user_id: str, page: PageParams, caller: ServiceCaller
) -> list[NoteOut]:
    interview, _, member = await key_member(company_id, interview_id, user_id)

    return await interview_notes.page(interview, member, page.offset, page.limit)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_note(
    company_id: UUID, interview_id: UUID, body: NoteIn, user_id: str, caller: ServiceCaller
) -> NoteOut:
    interview, company, member = await key_member(company_id, interview_id, user_id)

    return await interview_notes.add(interview, company, member, body.text, VIA_API)
