"""The team's notes on an interview (companies' note events): every member but the author hears
of a new note in the bell, grouped per interview while unread; the company's Slack channel gets
each note; the activity digest gets each new note's start (pending_notes). Each event is safe to
repeat and to come in any order: a note's events take turns (its lock), a new note is told once
(its mark in Received), the newest edit wins, and a deleted note (or its interview, or company)
is marked, so a late event about it tells nobody and the digest drops it."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events.notes import NoteDeleted, NoteWritten
from testee_common.events.notifications import NotificationKind, Recipient

from notifications.config import settings
from notifications.constants.notes import (
    DELETED_INTERVIEW_KEY,
    DELETED_NOTE_KEY,
    NOTES_LINK,
    PENDING_NOTE_HOURS,
)
from notifications.core.db import Session
from notifications.helpers.notes import excerpt, first_item, with_note, without_note
from notifications.helpers.slack import note_message
from notifications.integrations import companies
from notifications.repositories import note_notices, notifications, pending_notes
from notifications.services import slack
from notifications.services.feed import announce

logger = logging.getLogger(__name__)


def as_data(event: NoteWritten) -> dict:
    return {
        **event.model_dump(),
        "note_id": str(event.note_id),
        "company_id": str(event.company_id),
        "interview_id": str(event.interview_id),
    }


async def gone(session: AsyncSession, note: dict) -> bool:
    """Whether the note, its interview or its company was deleted."""
    marks = (
        DELETED_NOTE_KEY.format(note_id=note["note_id"]),
        DELETED_INTERVIEW_KEY.format(interview_id=note["interview_id"]),
    )

    for mark in marks:
        if await notifications.has_received(session, mark):
            return True

    return await notifications.is_deleted(session, f"{Recipient.COMPANY}:{note['company_id']}")


async def readers(note: dict) -> list[str]:
    """The company's members but the note's author, in a fixed order (they're locked in it);
    none once the company is gone."""
    found = await companies.members([note["company_id"]])
    user_ids = {
        member["user_id"]
        for company in found
        for member in company["members"]
        if member.get("user_id") and member["user_id"] != note["author_id"]
    }

    return sorted(user_ids)


async def tell(session: AsyncSession, note: dict, user_ids: list[str], now: datetime) -> None:
    """Each reader's unread item about the interview's notes gets the note, or a new item
    starts; the reader's oldest go past the bell's limits."""
    link = NOTES_LINK.format(company_id=note["company_id"], interview_id=note["interview_id"])

    for user_id in user_ids:
        recipient = {"recipient": Recipient.USER, "recipient_id": user_id}
        await notifications.lock_recipient(session, f"{Recipient.USER}:{user_id}")
        group = await note_notices.unread_group(session, user_id, link)

        if group is None:
            await note_notices.add(session, user_id, link, first_item(note), now)
        else:
            group.data = with_note(group.data, note)
            group.created_at = now

        await notifications.prune(session, recipient, now)


async def written(event: NoteWritten, created: bool) -> None:
    """A note written (`created`) or edited. The digest keeps its newest text; a new one is told
    to the other members' bells once (then their open tabs hear of it) and posted to Slack."""
    note = as_data(event)
    now = datetime.now(UTC)
    user_ids = await readers(note) if created else []
    told = False

    async with Session.begin() as session:
        await note_notices.lock_note(session, note["note_id"])
        await notifications.lock_recipient(session, f"{Recipient.COMPANY}:{note['company_id']}")

        if await gone(session, note):
            return

        since = now - timedelta(hours=PENDING_NOTE_HOURS)
        await pending_notes.save(session, note, excerpt(note["text"]), since)

        if created and await notifications.claim(session, f"note:{note['note_id']}", now):
            await tell(session, note, user_ids, now)
            told = True

    if told:
        await announce_to(user_ids)

    if created:
        await post_to_slack(note)


async def announce_to(user_ids: list[str]) -> None:
    """Their open tabs reload the bell; one that misses it sees the item on its next load."""
    for user_id in user_ids:
        try:
            await announce(Recipient.USER, user_id)
        except Exception:
            logger.exception("Couldn't announce a note to %s", user_id)


async def post_to_slack(note: dict) -> None:
    """Each note goes to the company's channel once, if it takes notes."""
    if not slack.available():
        return

    kind = NotificationKind.NOTE_ADDED
    webhook = await slack.channel(note["company_id"], kind)

    if webhook is not None:
        message = note_message(note, settings.site_url)
        await slack.post_once(note["company_id"], webhook, f"note:{note['note_id']}", message, kind)


async def deleted(event: NoteDeleted) -> None:
    """A deleted note is marked, leaves the bell items that hold it (an item left without notes
    goes) and the digest. Safe to repeat."""
    note_id = str(event.note_id)
    now = datetime.now(UTC)

    async with Session.begin() as session:
        await note_notices.lock_note(session, note_id)
        await notifications.claim(session, DELETED_NOTE_KEY.format(note_id=note_id), now)
        items = await note_notices.holding(
            session, str(event.interview_id), {"notes": [{"id": note_id}]}
        )

        for item in items:
            notes, count = without_note(item.data, note_id)
            await note_notices.set_notes(session, item, notes, count)

        await pending_notes.remove(session, note_id)


async def remove_interview(company_id: str, interview_id: str) -> None:
    """A deleted interview takes its notes: they leave the bell and the digest, and a late event
    about one tells nobody. Its company's lock, which a note's events take too, keeps one from
    slipping in meanwhile. Safe to repeat."""
    async with Session.begin() as session:
        await notifications.lock_recipient(session, f"{Recipient.COMPANY}:{company_id}")
        mark = DELETED_INTERVIEW_KEY.format(interview_id=interview_id)
        await notifications.claim(session, mark, datetime.now(UTC))
        await note_notices.remove_interview(session, interview_id)
        await pending_notes.remove_interview(session, interview_id)
