from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from testee_common.auth.auth import CurrentUser
from testee_common.db.paging import PageParams

from companies.constants.invites import MAX_SEARCH_LENGTH
from companies.schemas.invites import CompanyCandidateOut
from companies.services import candidate_results
from companies.services.access import require_company

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
