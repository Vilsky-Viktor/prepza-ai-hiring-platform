from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import EmailStr

from app.auth import needs
from app.config.settings import settings
from app.constants.permissions import Permission
from app.helpers.public import candidate_of
from app.integrations import companies
from app.models.api import ApiKey
from app.schemas.changes import Credits
from app.schemas.public import Candidate

# What's the company's as a whole: its candidates across interviews and its credits.
router = APIRouter(
    tags=["Company"],
    responses={
        401: {
            "description": "The API key is missing, invalid or expired, or its creator can no longer use it"
        },
        403: {
            "description": (
                "The API key doesn't have the permission the endpoint needs (`code` is "
                "`missing_permission`)"
            )
        },
        429: {"description": "Your company's keys exceeded 60 requests per minute"},
    },
)


@router.get("/candidates", summary="Find a candidate by email")
async def find_candidates(
    email: Annotated[EmailStr, Query(description="The email the candidate was invited with")],
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_READ)],
) -> list[Candidate]:
    """The candidates invited with this email in any of your company's interviews, newest
    first, each with its interview's `interview_id`."""
    found = await companies.find_candidates(key.company_id, str(email))

    return [
        candidate_of(row, key.company_id, UUID(row["interview_id"]), settings.site_url)
        for row in found
    ]


@router.get("/credits", summary="Read your credits")
async def get_credits(key: Annotated[ApiKey, needs(Permission.CREDITS_READ)]) -> Credits:
    """Your company's credits: a candidate costs 500, set aside when they're invited."""
    return Credits(**await companies.credits(key.company_id))
