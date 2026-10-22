from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Response, status
from prepza_common.paging import PageParams

from app.auth import needs
from app.config.settings import settings
from app.constants.permissions import Permission
from app.constants.responses import COMMON, NOT_FOUND, RETRY_AFTER
from app.helpers.docs import refusal
from app.helpers.public import candidate_of, interview_of
from app.integrations import companies
from app.models.api import ApiKey
from app.schemas.changes import InterviewIn
from app.schemas.public import Candidate, CandidateIn, Interview
from app.schemas.public_params import After, IdempotencyKey, UpdatedSince
from app.services.idempotency import fingerprint, once, slot

# Every route can answer COMMON; ones under an interview also NOT_FOUND.
router = APIRouter(prefix="/interviews", tags=["Interviews"], responses=COMMON)


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
        200: {
            "model": Candidate,
            "description": "Already invited or finished: the candidate as they are",
        },
        **NOT_FOUND,
        402: refusal("The company doesn't have enough credits (`insufficient_credits`)"),
        409: refusal(
            "The interview's questions are still being generated (`interview_not_ready`), the "
            "company is suspended (`company_suspended`), or the same request is still running "
            "(`request_in_progress`)"
        ),
        422: refusal(
            "The body is invalid (`validation_failed`), or `return_url` isn't an https address "
            "on the company's verified website domain (`return_url_off_domain`)"
        ),
        429: {
            **refusal(
                "The key's creator reached their email limits, or the key its rate limit "
                "(`rate_limited`)"
            ),
            "headers": RETRY_AFTER,
        },
    },
)
async def invite_candidate(
    interview_id: UUID,
    body: CandidateIn,
    key: Annotated[ApiKey, needs(Permission.CANDIDATES_INVITE)],
    response: Response,
    idempotency_key: IdempotencyKey = None,
) -> Candidate:
    """Invites the candidate to the interview on behalf of the key's creator and reserves credits
    for them, with their name if given. By default prepza emails the invitation and the
    candidate signs in with that email; with `sign_in` false, your platform sends them to the
    response's `invite_url`, which opens the interview without signing in. With a `return_url`,
    the finished page takes the candidate back to your platform. Retrying is safe: inviting an
    address whose invite is still open, or who already finished, returns that candidate as they
    are (`200`), without another email or credits; an expired invite is sent again. To send an
    open invite again, use the resend endpoint."""
    await companies.interview(key.company_id, interview_id)

    created = True

    async def invite() -> str:
        nonlocal created
        invite_id, created = await companies.invite(
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

    request = fingerprint("invite", interview_id, body.model_dump(mode="json"))
    name, seconds = slot(key.company_id, key.id, idempotency_key, request)

    if idempotency_key:
        invite_id = UUID(await once(name, seconds, request, invite))
    else:
        invite_id = UUID(await invite())

    if not created:
        response.status_code = status.HTTP_200_OK

    found = await companies.candidate(key.company_id, interview_id, invite_id)

    return candidate_of(found, key.company_id, interview_id, settings.site_url)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an interview",
    responses={
        409: refusal(
            "The same request is still running (`request_in_progress`), or your company has as "
            "many interviews without candidates as it may (`interview_quota_reached`)"
        ),
        422: refusal("The body is invalid (`validation_failed`)"),
        429: {
            **refusal(
                "Your company or the key's creator made as many today as it may (`rate_limited`)"
            ),
            "headers": RETRY_AFTER,
        },
        503: refusal(
            "Making interviews is paused (`paused`), or today's AI budget is used up "
            "(`ai_budget_used_up`)"
        ),
    },
)
async def create_interview(
    body: InterviewIn,
    key: Annotated[ApiKey, needs(Permission.INTERVIEWS_CREATE)],
    idempotency_key: IdempotencyKey = None,
) -> Interview:
    """Makes an interview from a job description, as the key's creator would. Its questions take
    a few minutes: until `ready` is true, it can't take candidates; the `interview.ready` web
    hook event says when it is. Retrying is safe: the same request from the same key within 15
    minutes returns the interview the first one made."""

    async def create() -> str:
        made = await companies.create_interview(
            key.company_id, body.job_description, body.language, key.created_by
        )

        return made["id"]

    request = fingerprint("interview", body.model_dump(mode="json"))
    name, seconds = slot(key.company_id, key.id, idempotency_key, request)
    interview_id = UUID(await once(name, seconds, request, create))

    return interview_of(await companies.interview(key.company_id, interview_id))
