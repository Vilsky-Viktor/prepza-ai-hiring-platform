"""An interview's notes: every member reads and writes them; each edits only their own and
deletes their own, the owner and admins delete anyone's and pin one. Each change is saved with
its line in the action log (never the note's text)."""

import logging

import httpx
from fastapi import HTTPException, status
from prepza_common.auth.key_actor import actor_key
from prepza_common.events.audit_actions import AuditAction
from prepza_common.i18n.i18n import CodedError
from prepza_common.limits.rate_limit import hit_or_skip

from companies.constants import error_codes
from companies.constants.interview_notes import (
    NOTE_NOT_FOUND,
    ONLY_AUTHOR_DELETES,
    ONLY_AUTHOR_EDITS,
    ONLY_EDITORS_PIN,
)
from companies.core.db import Session
from companies.integrations import accounts, api_keys
from companies.integrations.redis import get_redis
from companies.models.companies import Company, Member
from companies.models.interview_notes import InterviewNote
from companies.models.interviews import Interview
from companies.repositories import audit, interview_notes
from companies.schemas.interview_notes import NoteAuthor, NoteOut
from companies.services.access import can_edit, suspension_refusal

logger = logging.getLogger(__name__)


async def profiles_of(members: list[Member]) -> dict[str, dict]:
    """The authors' names and pictures; without them when accounts can't be reached (the notes
    still show, by email)."""
    user_ids = sorted(
        {item.user_id for item in members if item.user_id and not actor_key(item.user_id)}
    )

    try:
        return await accounts.profiles(user_ids)
    except httpx.HTTPError:
        logger.warning("Accounts unreachable; %s note authors shown by email", len(user_ids))

        return {}


async def key_names(company_id, notes: list[InterviewNote]) -> dict[str, str]:
    """The current names of the API keys that wrote any of the notes."""
    return await api_keys.names(
        company_id, [note.author_key_id for note in notes if note.author_key_id]
    )


def is_author(note: InterviewNote, member: Member) -> bool:
    """Whether `member` wrote the note: a member by their membership, an API key by its id."""
    key = actor_key(member.user_id)

    if key is not None:
        return str(note.author_key_id) == key

    return note.author_member_id is not None and note.author_member_id == member.id


def author_of(
    note: InterviewNote, author: Member | None, profiles: dict[str, dict], keys: dict[str, str]
) -> NoteAuthor:
    if note.author_key_id is not None:
        return NoteAuthor(name=keys.get(str(note.author_key_id)), api_key=True)

    if author is None or author.user_id is None:
        return NoteAuthor(former=True)

    profile = profiles.get(author.user_id, {})

    return NoteAuthor(
        name=profile.get("name") or author.invited_email, photo_url=profile.get("photo_url")
    )


def note_out(
    note: InterviewNote,
    author: Member | None,
    member: Member,
    profiles: dict[str, dict],
    keys: dict[str, str],
) -> NoteOut:
    """The note as `member` sees it, with what they may do with it."""
    own = is_author(note, member)

    return NoteOut(
        id=note.id,
        text=note.text,
        author=author_of(note, author, profiles, keys),
        pinned=note.pinned,
        created_at=note.created_at,
        edited_at=note.edited_at,
        can_edit=own,
        can_delete=own or can_edit(member),
        can_pin=can_edit(member),
    )


async def page(interview: Interview, member: Member, offset: int, limit: int) -> list[NoteOut]:
    """A page of the interview's notes, the pinned one first, then newest first (the interview
    itself says how many it has)."""
    async with Session() as session:
        rows = await interview_notes.page(
            session, interview.company_id, interview.id, offset, limit
        )

    profiles = await profiles_of([author for _, author in rows if author is not None])
    keys = await key_names(interview.company_id, [note for note, _ in rows])

    return [note_out(note, author, member, profiles, keys) for note, author in rows]


def refuse_if_suspended(company: Company) -> None:
    """A suspended company's notes can be read, not changed (409, as inviting is)."""
    if refusal := suspension_refusal(company):
        raise CodedError(status.HTTP_409_CONFLICT, refusal, error_codes.COMPANY_SUSPENDED)


async def add(
    interview: Interview, company: Company, member: Member, text: str, via: str | None = None
) -> NoteOut:
    """Any member writes one, within their hourly notes (429); not in a suspended company."""
    refuse_if_suspended(company)
    await hit_or_skip(
        get_redis(),
        f"rate:notes:{member.user_id}",
        "NOTES_PER_USER_HOUR",
        company_id=company.id,
        user_id=member.user_id,
    )

    async with Session.begin() as session:
        note = await interview_notes.add(
            session, interview, member.id, actor_key(member.user_id), text
        )
        await audit.record_interview(
            session, interview, member.user_id, AuditAction.NOTE_ADDED, via
        )

    return await own_note_out(interview, note, member)


async def own_note_out(interview: Interview, note: InterviewNote, member: Member) -> NoteOut:
    """A note `member` just wrote or changed, as they see it."""
    keys = await key_names(interview.company_id, [note])

    return note_out(note, member, member, await profiles_of([member]), keys)


async def found(interview: Interview, note_id) -> InterviewNote:
    async with Session() as session:
        note = await interview_notes.get(session, interview.id, note_id)

    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOTE_NOT_FOUND)

    return note


async def edit(
    interview: Interview, company: Company, member: Member, note_id, text: str
) -> NoteOut:
    """Only its author changes its text (403)."""
    refuse_if_suspended(company)

    async with Session.begin() as session:
        note = await interview_notes.get(session, interview.id, note_id)

        if note is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, NOTE_NOT_FOUND)

        if not is_author(note, member):
            raise HTTPException(status.HTTP_403_FORBIDDEN, ONLY_AUTHOR_EDITS)

        await interview_notes.set_text(session, note, text)
        await audit.record_interview(session, interview, member.user_id, AuditAction.NOTE_EDITED)

    return await own_note_out(interview, note, member)


async def delete(interview: Interview, company: Company, member: Member, note_id) -> None:
    """Its author, the owner or an admin deletes it, for good (403 for anyone else)."""
    refuse_if_suspended(company)
    note = await found(interview, note_id)

    if not is_author(note, member) and not can_edit(member):
        raise HTTPException(status.HTTP_403_FORBIDDEN, ONLY_AUTHOR_DELETES)

    async with Session.begin() as session:
        await interview_notes.remove(session, note.id)
        await audit.record_interview(session, interview, member.user_id, AuditAction.NOTE_DELETED)


async def pin(
    interview: Interview, company: Company, member: Member, note_id, pinned: bool
) -> None:
    """The owner or an admin pins a note, unpinning the interview's other one, or unpins it
    (403 for a viewer)."""
    refuse_if_suspended(company)

    if not can_edit(member):
        raise HTTPException(status.HTTP_403_FORBIDDEN, ONLY_EDITORS_PIN)

    note = await found(interview, note_id)

    if note.pinned == pinned:
        return

    action = AuditAction.NOTE_PINNED if pinned else AuditAction.NOTE_UNPINNED

    async with Session.begin() as session:
        await interview_notes.set_pinned(session, interview.id, note.id, pinned)
        await audit.record_interview(session, interview, member.user_id, action)
