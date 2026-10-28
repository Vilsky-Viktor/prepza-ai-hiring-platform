"""Notifications' events: emails to send, notifications to store, a Resend web hook's work and
deletions (rule 11: each is safe to repeat; an email carries the event's id as its idempotency
key, a notification its key, and deleting twice deletes nothing more)."""

from notifications.constants.events import (
    CANDIDATE_INTERVIEW_DELETED,
    CANDIDATE_INVITED,
    CANDIDATE_JOINED,
    CANDIDATE_REMINDED,
    CANDIDATE_REMOVED,
    COMPANY_DELETED,
    CONTACT_SENT,
    EMAIL_WEBHOOK,
    MEMBER_INVITED,
    NEWS_DELETED,
    NOTIFICATION_REQUESTED,
    REPORT_SHARED,
)
from notifications.handlers import (
    candidate_interview_deleted,
    candidate_invited,
    candidate_joined,
    candidate_reminded,
    candidate_removed,
    company_deleted,
    contact_sent,
    email_webhook,
    member_invited,
    news_deleted,
    notification_requested,
    report_shared,
)

HANDLERS = {
    NOTIFICATION_REQUESTED: notification_requested.handle,
    EMAIL_WEBHOOK: email_webhook.handle,
    CANDIDATE_INVITED: candidate_invited.handle,
    CANDIDATE_JOINED: candidate_joined.handle,
    CANDIDATE_REMINDED: candidate_reminded.handle,
    MEMBER_INVITED: member_invited.handle,
    REPORT_SHARED: report_shared.handle,
    COMPANY_DELETED: company_deleted.handle,
    CANDIDATE_REMOVED: candidate_removed.handle,
    CANDIDATE_INTERVIEW_DELETED: candidate_interview_deleted.handle,
    NEWS_DELETED: news_deleted.handle,
    CONTACT_SENT: contact_sent.handle,
}


async def handle(event_type: str, data: dict, event_id: str) -> None:
    """Sends the email or stores the notification an event asks for, and does a Resend web
    hook's work (each step safe to repeat); other events aren't ours."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(data, event_id)
