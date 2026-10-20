from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, status
from prepza_common.paging import PageParams

from app.auth import needs
from app.config.settings import settings
from app.constants.permissions import Permission
from app.helpers.public import candidate_of, interview_of
from app.integrations import companies
from app.models.api import ApiKey
from app.schemas.changes import CandidateUpdate, InterviewIn
from app.schemas.public import Candidate, CandidateIn, Interview
from app.services.idempotency import once

# Every route can answer these; ones under an interview also 404 (NOT_FOUND).
router = APIRouter(
    prefix="/interviews",
    tags=["Interviews"],
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
NOT_FOUND = {404: {"description": "The interview or candidate doesn't exist in your company"}}
UpdatedSince = Annotated[
    datetime | None,
    Query(
        description=(
            "Only items that changed at this time or later (ISO 8601), oldest change first: "
            "pass the last `updated_at` you got to sync"
        )
    ),
]
After = Annotated[
    UUID | None,
    Query(
        description=(
            "With `updated_since`: the `id` of the last item you got, so the next page starts "
            "after it and items changed at the same moment are neither repeated nor missed"
        )
    ),
]
IdempotencyKey = Annotated[
    str | None,
    Header(
        max_length=255,
        description=(
            "Any unique string, such as a UUID: a retry with the same key within 24 hours gets "
            "the first request's result instead of doing it again"
        ),
    ),
]


@router.get("", summary="List interviews")
async def list_interviews(
    key: Annotated[ApiKey, needs(Permission.INTERVIEWS_READ)],
    page: PageParams,
    updated_since: UpdatedSince = None,
    after: After = None,
) -> list[Interview]:
    """Returns your company's interviews, newest first; with `updated_since`, the ones that
    changed since, oldest change first."""
    found = await companies.interviews(
        key.company_id, page.offset, page.limit, updated_since, after
    )

    return [interview_of(item) for item in found]


@router.get("/{interview_id}", summary="Get an interview", responses=NOT_FOUND)
async def get_interview(
    interview_id: UUID, key: Annotated[ApiKey, needs(Permission.INTERVIEWS_READ)]
) -> Interview:
    """Returns one of your company's interviews."""
    return interview_of(await companies.interview(key.company_id, interview_id))


@router.get(
    "/{interview_id}/candidates",
    summary="List candidates",
    tags=["Candidates"],
    responses=NOT_FOUND,
)
async def list_candidates(
    interview_id: UUID,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_READ)],
    page: PageParams,
    updated_since: UpdatedSince = None,
    after: After = None,
) -> list[Candidate]:
    """Returns the interview's candidates with their progress and results, newest first; with
    `updated_since`, the ones that changed since, oldest change first."""
    found = await companies.candidates(
        key.company_id, interview_id, page.offset, page.limit, updated_since, after
    )

    return [candidate_of(item, key.company_id, interview_id, settings.site_url) for item in found]


@router.get(
    "/{interview_id}/candidates/{candidate_id}",
    summary="Get a candidate",
    tags=["Candidates"],
    responses=NOT_FOUND,
)
async def get_candidate(
    interview_id: UUID,
    candidate_id: UUID,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_READ)],
) -> Candidate:
    """Returns one candidate of the interview with their progress and results."""
    found = await companies.candidate(key.company_id, interview_id, candidate_id)

    return candidate_of(found, key.company_id, interview_id, settings.site_url)


@router.post(
    "/{interview_id}/candidates",
    status_code=status.HTTP_201_CREATED,
    summary="Invite a candidate",
    tags=["Candidates"],
    responses={
        **NOT_FOUND,
        402: {"description": "The company doesn't have enough credits"},
        409: {"description": "The interview's questions are still being generated"},
        422: {
            "description": (
                "The body is invalid, or `return_url` isn't an https address on the company's "
                "verified website domain"
            )
        },
        429: {
            "description": "The key's creator reached their email limits, or the key its rate limit"
        },
        503: {"description": "Invitations are temporarily paused"},
    },
)
async def invite_candidate(
    interview_id: UUID,
    body: CandidateIn,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_INVITE)],
    idempotency_key: IdempotencyKey = None,
) -> Candidate:
    """Invites the candidate to the interview on behalf of the key's creator and reserves credits
    for them, with their name if given. By default prepza emails the invitation and the
    candidate signs in with that email; with `sign_in` false, your platform sends them to the
    response's `invite_url`, which opens the interview without signing in. With a `return_url`,
    the finished page takes the candidate back to your platform. Inviting an address that was
    already invited sends the invitation again, if emails are on; one who already finished is
    returned as they are, without an email."""
    await companies.interview(key.company_id, interview_id)

    async def invite() -> str:
        invite_id = await companies.invite(
            interview_id,
            str(body.email),
            key.created_by,
            body.name,
            body.return_url,
            body.sign_in,
            # Companies keeps only a theme that's enforced.
            None if body.theme == "default" else body.theme,
        )

        return str(invite_id)

    invite_id = UUID(await once(key.company_id, idempotency_key, invite))
    found = await companies.candidate(key.company_id, interview_id, invite_id)

    return candidate_of(found, key.company_id, interview_id, settings.site_url)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an interview",
    responses={
        409: {
            "description": (
                "A request with this Idempotency-Key is still running, or your company has as "
                "many interviews without candidates as it may"
            )
        },
        422: {"description": "The body is invalid"},
        429: {"description": "Your company or the key's creator made as many today as it may"},
        503: {"description": "Making interviews is paused, or today's AI budget is used up"},
    },
)
async def create_interview(
    body: InterviewIn,
    key: Annotated[ApiKey, needs(Permission.INTERVIEWS_CREATE)],
    idempotency_key: IdempotencyKey = None,
) -> Interview:
    """Makes an interview from a job description, as the key's creator would. Its questions take
    a few minutes: until `ready` is true, it can't take candidates; the `interview.ready` web
    hook event says when it is."""

    async def create() -> str:
        made = await companies.create_interview(
            key.company_id, body.job_description, body.language, key.created_by
        )

        return made["id"]

    interview_id = UUID(await once(key.company_id, idempotency_key, create))

    return interview_of(await companies.interview(key.company_id, interview_id))


@router.patch(
    "/{interview_id}/candidates/{candidate_id}",
    summary="Update a candidate",
    responses={
        **NOT_FOUND,
        409: {"description": "Extra time was asked for a candidate who already started"},
        422: {"description": "The body is invalid"},
    },
)
async def update_candidate(
    interview_id: UUID,
    candidate_id: UUID,
    body: CandidateUpdate,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_CHANGE)],
) -> Candidate:
    """Corrects the candidate's name, or gives them extra time on each question before they
    start, as an accommodation."""
    if "name" in body.model_fields_set:
        await companies.rename_candidate(
            key.company_id, interview_id, candidate_id, body.name or "", key.created_by
        )

    if body.extra_time is not None:
        await companies.set_extra_time(
            key.company_id, interview_id, candidate_id, body.extra_time, key.created_by
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
    await companies.remove_candidate(key.company_id, interview_id, candidate_id, key.created_by)


@router.post(
    "/{interview_id}/candidates/{candidate_id}/resend",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Send the invitation again",
    responses={
        **NOT_FOUND,
        409: {
            "description": (
                "The candidate already finished, or was invited with `sign_in` false (prepza "
                "doesn't email them)"
            )
        },
        429: {"description": "The key's creator reached their email limits"},
    },
)
async def resend_invite(
    interview_id: UUID,
    candidate_id: UUID,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_INVITE)],
) -> None:
    """Emails the candidate their invitation again, as a reminder; an expired invitation comes
    back to life for another 30 days."""
    await companies.resend(key.company_id, interview_id, candidate_id, key.created_by)
