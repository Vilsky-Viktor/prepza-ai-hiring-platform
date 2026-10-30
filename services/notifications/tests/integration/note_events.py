# The team's note events, as companies saves them, for the notes' integration tests.
import uuid
from datetime import UTC, datetime

from prepza_common.events.notes import NOTE_CREATED, NOTE_DELETED, NOTE_EDITED


def note(company_id: str, interview_id: str, author: str, text: str, **fields) -> dict:
    """A note's `company.note_created` data; `fields` override its id, title, times, name."""
    return {
        "note_id": str(uuid.uuid4()),
        "company_id": company_id,
        "interview_id": interview_id,
        "title": "AI Engineer",
        "author_id": author,
        "author_name": author.title(),
        "text": text,
        "created_at": datetime.now(UTC).isoformat(),
        "edited_at": None,
        **fields,
    }


def created(data: dict, event_id: str | None = None) -> tuple:
    return NOTE_CREATED, data, event_id or str(uuid.uuid4())


def edited(data: dict, text: str, at: datetime) -> tuple:
    return NOTE_EDITED, {**data, "text": text, "edited_at": at.isoformat()}, str(uuid.uuid4())


def deleted(data: dict) -> tuple:
    keys = ("note_id", "company_id", "interview_id")

    return NOTE_DELETED, {key: data[key] for key in keys}, str(uuid.uuid4())
