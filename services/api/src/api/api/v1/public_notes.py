from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from prepza_common.config.constants import MAX_PAGE_SIZE
from prepza_common.db.paging import PageParams

from api.api.dependencies import needs
from api.constants.permissions import Permission
from api.constants.responses import COMMON, LISTED, NOT_FOUND, RETRY_AFTER
from api.helpers.docs import refusal
from api.helpers.public import link_next, note_of
from api.integrations import companies
from api.models.api import ApiKey
from api.schemas.changes import NoteIn
from api.schemas.public import Note
from api.schemas.public_params import IdempotencyKey
from api.services.idempotency import fingerprint, once, slot

# An interview's notes: what its team writes about the hiring round, never shown to candidates.
router = APIRouter(prefix="/interviews", tags=["Notes"], responses=COMMON)


@router.get("/{interview_id}/notes", summary="List notes", responses={200: LISTED, **NOT_FOUND})
async def list_notes(
    interview_id: UUID,
    key: Annotated[ApiKey, needs(Permission.NOTES_READ)],
    page: PageParams,
    request: Request,
    response: Response,
) -> list[Note]:
    """Returns the notes your team wrote on the interview: the pinned one first, then newest
    first. A full page comes with a `Link` header to the next one (`rel="next"`)."""
    found = await companies.notes(
        key.company_id, interview_id, key.created_by, page.offset, page.limit
    )
    listed = [note_of(item) for item in found]
    link_next(request, response, page.offset, page.limit, listed, False)

    return listed


@router.post(
    "/{interview_id}/notes",
    status_code=status.HTTP_201_CREATED,
    summary="Add a note",
    responses={
        200: {
            "model": Note,
            "description": "A retry within 15 minutes: the note the first request added",
        },
        403: refusal(
            "The API key doesn't have the permission (`missing_permission`) or doesn't allow the "
            "address (`ip_not_allowed`)"
        ),
        **NOT_FOUND,
        409: refusal(
            "The same request is still running (`request_in_progress`), or your company is "
            "suspended (`company_suspended`)"
        ),
        422: refusal("The body is invalid (`validation_failed`)"),
        429: {
            **refusal(
                "The key's creator added as many notes this hour as they may (`rate_limited`)"
            ),
            "headers": RETRY_AFTER,
        },
    },
)
async def add_note(
    interview_id: UUID,
    body: NoteIn,
    key: Annotated[ApiKey, needs(Permission.NOTES_ADD)],
    response: Response,
    idempotency_key: IdempotencyKey = None,
) -> Note:
    """Adds a note to the interview on behalf of the key's creator, for your team to read in
    prepza; candidates never see it. Retrying is safe: the same request from the same key within
    15 minutes returns the note the first one added, with `200`."""
    created = None

    async def add() -> str:
        nonlocal created
        created = await companies.add_note(key.company_id, interview_id, body.text, key.created_by)

        return created["id"]

    request = fingerprint("note", interview_id, body.model_dump(mode="json"))
    name, seconds = slot(key.company_id, key.id, idempotency_key, request)
    note_id = await once(name, seconds, request, add)

    if created is not None:
        return note_of(created)

    # A retry: the note the first request added, among the newest.
    response.status_code = status.HTTP_200_OK
    found = await companies.notes(key.company_id, interview_id, key.created_by, 0, MAX_PAGE_SIZE)
    first = next((item for item in found if item["id"] == note_id), None)

    if first is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")

    return note_of(first)
