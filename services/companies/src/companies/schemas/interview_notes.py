from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints
from testee_common.config.constants import MAX_NOTE_LENGTH

# A note's text: plain text with its line breaks, without leading or trailing blanks.
NoteText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_NOTE_LENGTH)
]


class NoteIn(BaseModel):
    text: NoteText = Field(description="The note, as plain text; line breaks are kept.")


class PinIn(BaseModel):
    pinned: bool = Field(description="True pins the note (unpinning any other); false unpins it.")


class NoteAuthor(BaseModel):
    """Who wrote a note: their name (or email without one) and picture; `former` when they're no
    longer a member, with neither. An API key that wrote one (`api_key`) has its name as it is
    now, None once it was deleted."""

    name: str | None = None
    photo_url: str | None = None
    former: bool = False
    api_key: bool = False


class NoteOut(BaseModel):
    id: UUID
    text: str
    author: NoteAuthor
    pinned: bool
    created_at: datetime
    # When its text last changed; None if it never did.
    edited_at: datetime | None
    # What the signed-in member may do with it: the author edits; the author, the owner and
    # admins delete; the owner and admins pin.
    can_edit: bool = False
    can_delete: bool = False
    can_pin: bool = False
