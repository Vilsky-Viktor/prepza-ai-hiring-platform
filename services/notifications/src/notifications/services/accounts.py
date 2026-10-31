# What other services ask of notifications about a user's account or a company: deleting them,
# and a user's data export.
from datetime import UTC, datetime

from fastapi.encoders import jsonable_encoder
from testee_common.events.notifications import Recipient

from notifications.core.db import Session
from notifications.helpers.notes import without_author
from notifications.repositories import (
    bulk_recipients,
    note_notices,
    notifications,
    opt_outs,
    pending_notes,
    sent_emails,
    slack,
)
from notifications.schemas.notifications import NotificationOut
from notifications.services import slack as slack_service


async def remove_user(user_id: str, email: str) -> None:
    """The user's own notifications go, and companies' notifications about them as a candidate
    (their email and grade), and owners' notifications that they joined a company (their email);
    the Slack channels they connected stay with their companies, without their id. The log of
    digests and reminders sent to them goes too, and their rows in bulk sends; the notes they
    wrote stay their companies', in others' bells and digests as a former member's. All of it
    is one save; then each company whose channel stopped working is told it needs
    reconnecting."""
    async with Session.begin() as session:
        await notifications.remove_user(session, user_id)
        await forget_author(session, user_id)
        await sent_emails.remove_user(session, user_id)
        await bulk_recipients.remove_user(session, user_id)
        await notifications.remove_candidate(session, email)
        await notifications.remove_member(session, email)
        stopped = await slack.forget_maker(session, user_id)

    for company_id in stopped:
        await slack_service.stopped(company_id)


async def forget_author(session, user_id: str) -> None:
    """Notes by a deleted account show as a former member's."""
    for item in await note_notices.by_author(session, user_id):
        notes = without_author(item.data, user_id)
        await note_notices.set_notes(session, item, notes, item.data.get("count", 1))

    await pending_notes.forget_author(session, user_id)


async def export(user_id: str) -> dict:
    """The user's own notifications, when they last opened them, the Slack channels they
    connected, the log of digests and reminders sent to them, and the notices and campaigns they
    were sent (with what became of each)."""
    async with Session() as session:
        items = await notifications.latest(session, [(Recipient.USER, user_id)], limit=None)
        seen_at = await notifications.seen_at(session, user_id)
        channels = await slack.made_by(session, user_id)
        sent = await sent_emails.of_user(session, user_id)
        bulk = await bulk_recipients.of_user(session, user_id)

    return jsonable_encoder(
        {
            "notifications": [NotificationOut.model_validate(item) for item in items],
            "slack_channels": [
                {
                    "company_id": row.company_id,
                    "team": row.team,
                    "channel": row.channel,
                    "at": row.created_at,
                }
                for row in channels
            ],
            "notifications_last_opened": seen_at,
            "emails_sent": [
                {"kind": row.kind, "about": row.key, "on": row.sent_on} for row in sent
            ],
            "emails_to_many": [
                {
                    "kind": send.kind,
                    "about": send.about,
                    "status": row.status,
                    "sent_at": row.sent_at,
                    "unsubscribed_at": row.unsubscribed_at,
                    "complained_at": row.complained_at,
                }
                for send, row in bulk
            ],
        }
    )


async def remove_company(company_id: str) -> None:
    """A deleted company's notifications go (and it gets none after), its members' items about
    its notes and the notes waiting for the digest, with its candidates' opt-outs, in one save;
    then its Slack channel, and testee's app unless another company uses it. Safe to repeat."""
    async with Session.begin() as session:
        await notifications.remove_company(session, company_id, datetime.now(UTC))
        await note_notices.remove_company(session, company_id)
        await pending_notes.remove_company(session, company_id)
        await opt_outs.remove_company(session, company_id)

    await slack_service.disconnect(company_id)
