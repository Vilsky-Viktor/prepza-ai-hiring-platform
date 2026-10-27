from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import EmailStr

from api.api.dependencies import needs
from api.config import settings
from api.constants.api import EMAIL_QUERY_DEPRECATED_AT, EMAIL_QUERY_SUNSET_AT
from api.constants.permissions import Permission
from api.constants.responses import COMMON, DEPRECATION_HEADERS
from api.helpers.public import candidate_of, deprecation_headers
from api.integrations import companies
from api.models.api import ApiKey
from api.schemas.changes import CandidateSearch, Credits
from api.schemas.public import Candidate

# What's the company's as a whole: its candidates across interviews and its credits.
router = APIRouter(tags=["Company"], responses=COMMON)


@router.post("/candidates/search", summary="Find a candidate by email")
async def search_candidates(
    body: CandidateSearch, key: Annotated[ApiKey, needs(Permission.CANDIDATES_READ)]
) -> list[Candidate]:
    """The candidates invited with this email in any of your company's interviews, newest
    first, at most 100, each with its interview's `interview_id`. The email goes in the body, so
    it stays out of URLs and the logs that keep them."""
    return await found_by_email(key, str(body.email))


@router.get(
    "/candidates",
    summary="Find a candidate by email (deprecated)",
    deprecated=True,
    responses={200: {"description": "Successful Response", "headers": DEPRECATION_HEADERS}},
)
async def find_candidates(
    email: Annotated[EmailStr, Query(description="The email the candidate was invited with")],
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_READ)],
    response: Response,
) -> list[Candidate]:
    """Use `POST /candidates/search`, which takes the email in the body: an email in a query
    string ends up in logs. This one works, answering as that does, until 1 May 2027, and says
    so in its `Deprecation`, `Sunset` and `Link` headers."""
    response.headers.update(
        deprecation_headers(EMAIL_QUERY_DEPRECATED_AT, EMAIL_QUERY_SUNSET_AT, settings.site_url)
    )

    return await found_by_email(key, str(email))


async def found_by_email(key: ApiKey, email: str) -> list[Candidate]:
    found = await companies.find_candidates(key.company_id, email)

    return [
        candidate_of(row, key.company_id, UUID(row["interview_id"]), settings.site_url)
        for row in found
    ]


@router.get("/credits", summary="Read your credits")
async def get_credits(key: Annotated[ApiKey, needs(Permission.CREDITS_READ)]) -> Credits:
    """Your company's credits: a candidate costs 500, set aside when they're invited."""
    return Credits(**await companies.credits(key.company_id))
