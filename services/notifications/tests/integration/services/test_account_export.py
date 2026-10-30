"""A user's data export from notifications, against the real database: the log of digests and
reminders sent to them, the notices and campaigns they were among the recipients of, and when
they last opened the bell, never another user's rows."""

import uuid
from datetime import UTC, date, datetime

from notifications.constants.bulk import BulkKind
from notifications.repositories import bulk_sends, notifications, sent_emails
from notifications.services import accounts
from tests.integration.transactions import transaction


def test_the_export_has_the_sent_log_the_emails_to_many_and_the_bells_last_opening(run):
    user, other, about = f"u-{uuid.uuid4()}", f"u-{uuid.uuid4()}", str(uuid.uuid4())
    opened = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)

    async def scenario():
        await transaction(sent_emails.mark, user, "digest", date(2026, 10, 21), [])
        await transaction(sent_emails.mark, other, "digest", date(2026, 10, 21), [])
        send_id = await transaction(bulk_sends.start, BulkKind.LEGAL_TERMS, about, "sam")
        await transaction(bulk_sends.save_page, send_id, "", f"x:{other}", [user, other], True)
        await transaction(notifications.mark_seen, user, opened)

        return await accounts.export(user)

    exported = run(scenario())

    assert exported["emails_sent"] == [
        {"kind": "digest", "about": "day:2026-10-21", "on": "2026-10-21"}
    ]
    assert [(row["kind"], row["about"], row["status"]) for row in exported["emails_to_many"]] == [
        (BulkKind.LEGAL_TERMS, about, "pending")
    ]
    assert exported["notifications_last_opened"].startswith("2026-10-20T09:00:00")
