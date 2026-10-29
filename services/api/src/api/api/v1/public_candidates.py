from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.key_actor import key_actor

from api.api.dependencies import needs
from api.config import settings
from api.constants.permissions import Permission
from api.constants.responses import COMMON, NOT_FOUND, RETRY_AFTER
from api.helpers.docs import refusal
from api.helpers.public import candidate_of
from api.integrations import companies
from api.models.api import ApiKey
from api.schemas.changes import CandidateUpdate
from api.schemas.public import Candidate

# What changes one candidate of an interview: their name and extra time, a reminder, removal.
router = APIRouter(prefix="/interviews", tags=["Candidates"], responses=COMMON)


@router.patch(
    "/{interview_id}/candidates/{candidate_id}",
    summary="Update a candidate",
    responses={
        **NOT_FOUND,
        409: refusal(
            "Extra time was asked for a candidate who already started (`candidate_started`)"
        ),
        422: refusal("The body is invalid (`validation_failed`)"),
    },
)
async def update_candidate(
    interview_id: UUID,
    candidate_id: UUID,
    body: CandidateUpdate,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_CHANGE)],
) -> Candidate:
    """Corrects the candidate's name, or gives them extra time on each question before they
    start, as an accommodation. All or nothing: when one change is refused, neither is made."""
    changes = {}

    if "name" in body.model_fields_set:
        changes["name"] = body.name or ""

    if body.extra_time is not None:
        changes["extra_time"] = body.extra_time

    # Both or neither: companies checks every rule before it writes.
    if changes:
        await companies.change_candidate(
            key.company_id, interview_id, candidate_id, changes, key_actor(key.id)
        )

    found = await companies.candidate(key.company_id, interview_id, candidate_id)

    return candidate_of(found, key.company_id, interview_id, settings.site_url)


@router.delete(
    "/{interview_id}/candidates/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a candidate",
    responses=NOT_FOUND,
)
async def remove_candidate(
    interview_id: UUID,
    candidate_id: UUID,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_DELETE)],
) -> None:
    """Withdraws an invite the candidate hasn't used yet: its link stops working and its credits
    come back. A candidate who started is erased for good, with their answers and results, for
    example when they ask to have their data deleted; one who answered at least one question is
    charged. Your web hooks get `candidate.removed`."""
    await companies.remove_candidate(key.company_id, interview_id, candidate_id, key_actor(key.id))


@router.post(
    "/{interview_id}/candidates/{candidate_id}/resend",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Send the invitation again",
    responses={
        **NOT_FOUND,
        409: refusal(
            "The candidate already finished (`candidate_finished`), or was invited with "
            "`sign_in` false, so prepza doesn't email them (`invited_without_sign_in`)"
        ),
        429: {
            **refusal("The key reached its email limits (`rate_limited`)"),
            "headers": RETRY_AFTER,
        },
    },
)
async def resend_invite(
    interview_id: UUID,
    candidate_id: UUID,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_INVITE)],
) -> None:
    """Emails the candidate their invitation again, as a reminder; an expired invitation comes
    back to life for another 30 days."""
    await companies.resend(key.company_id, interview_id, candidate_id, key_actor(key.id))
