"""The payloads of companies' events about an interview's team notes, which notifications consumes
to tell the team (the bell, Slack, the activity digest). They're in the `company.` family, which
notifications already takes whole: a family of their own wouldn't fit its Pub/Sub filter
(infra/terraform/pubsub.tf). Consumers ignore fields they don't know (tolerant reader); the newest
`edited_at` wins, whatever order the events come in."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

NOTE_CREATED = "company.note_created"
NOTE_EDITED = "company.note_edited"
NOTE_DELETED = "company.note_deleted"


class NoteWritten(BaseModel):
    """A note as it was just written (`company.note_created`) or edited (`company.note_edited`,
    with `edited_at`): its interview's title (None before the interview has one), its author's id
    (a user's id, or `key:<id>` for an API key, which writes as itself) and name as the team sees
    it (a member's name or email, a key's name), and its text."""

    model_config = ConfigDict(extra="ignore")

    note_id: UUID
    company_id: UUID
    interview_id: UUID
    title: str | None = None
    author_id: str | None = None
    author_name: str | None = None
    text: str
    created_at: datetime
    edited_at: datetime | None = None


class NoteDeleted(BaseModel):
    """A note was deleted for good."""

    model_config = ConfigDict(extra="ignore")

    note_id: UUID
    company_id: UUID
    interview_id: UUID
