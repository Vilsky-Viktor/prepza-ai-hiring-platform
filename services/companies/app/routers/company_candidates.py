from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from prepza_common.auth import CurrentUser
from prepza_common.paging import PageParams

from app.constants.invites import MAX_SEARCH_LENGTH
from app.schemas.invites import CompanyCandidateOut
from app.services import candidate_results
from app.services.access import require_company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/{company_id}/candidates")
async def search_candidates(
    company_id: UUID,
    user: CurrentUser,
    page: PageParams,
    q: Annotated[str, Query(max_length=MAX_SEARCH_LENGTH)] = "",
) -> list[CompanyCandidateOut]:
    """Finds candidates by name or email (`q`) across the company's interviews, newest first, a
    page at a time; to list an interview's candidates, use that interview's list instead. Any
    member, viewers too."""
    company, _ = await require_company(user, company_id)

    return await candidate_results.company_page(company.id, page.offset, page.limit, q.strip())
