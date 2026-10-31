from uuid import UUID

from fastapi import APIRouter, status
from testee_common.auth.auth import CurrentUser
from testee_common.db.paging import PageParams

from companies.schemas.interview_notes import NoteIn, NoteOut, PinIn
from companies.services import interview_notes
from companies.services.interview_access import interview_for

# An interview's notes, for its team: every member reads and writes them (interview_notes.py
# says who may change which).
router = APIRouter(prefix="/interviews/{interview_id}/notes", tags=["interviews"])


@router.get("")
async def list_notes(interview_id: UUID, user: CurrentUser, page: PageParams) -> list[NoteOut]:
    """The pinned note first, then newest first, each with what the user may do with it."""
    interview, _, member = await interview_for(user, interview_id)

    return await interview_notes.page(interview, member, page.offset, page.limit)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_note(interview_id: UUID, body: NoteIn, user: CurrentUser) -> NoteOut:
    interview, company, member = await interview_for(user, interview_id)

    return await interview_notes.add(interview, company, member, body.text)


@router.patch("/{note_id}")
async def edit_note(interview_id: UUID, note_id: UUID, body: NoteIn, user: CurrentUser) -> NoteOut:
    """Only the note's author changes its text."""
    interview, company, member = await interview_for(user, interview_id)

    return await interview_notes.edit(interview, company, member, note_id, body.text)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(interview_id: UUID, note_id: UUID, user: CurrentUser) -> None:
    """The note's author, the owner or an admin deletes it, for good."""
    interview, company, member = await interview_for(user, interview_id)
    await interview_notes.delete(interview, company, member, note_id)


@router.put("/{note_id}/pinned", status_code=status.HTTP_204_NO_CONTENT)
async def pin_note(interview_id: UUID, note_id: UUID, body: PinIn, user: CurrentUser) -> None:
    """The owner or an admin pins the note (unpinning any other) or unpins it."""
    interview, company, member = await interview_for(user, interview_id)
    await interview_notes.pin(interview, company, member, note_id, body.pinned)
