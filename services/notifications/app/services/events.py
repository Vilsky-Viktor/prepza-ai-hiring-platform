import logging

from app.config.settings import settings
from app.constants.events import (
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
from app.helpers.emails import (
    candidate_invite_email,
    candidate_joined_email,
    candidate_reminder_email,
    contact_email,
    member_invite_email,
    report_email,
)
from app.helpers.unsubscribe import address_hash
from app.models.email import Email
from app.services import delivery, service_emails, slack, webhooks
from app.services.feed import announce
from app.services.webhooks import report_undelivered
from app.storage import notifications, opt_outs

logger = logging.getLogger(__name__)


async def deliver(email: Email, event_id: str) -> None:
    # The event's id as the key (the outbox's, the same on a re-send, or Pub/Sub's), so a
    # retried or re-sent event never sends the email twice.
    await delivery.send(email, f"events/{event_id}")


async def notify(data: dict, event_id: str) -> None:
    """Stores a requested notification, tells the recipient's open tabs, and posts a new one to
    the company's Slack channel; one that adds to a group isn't posted again. A retried event is
    stored once and announced once (if announcing fails, the tabs see it on their next load) and
    posted once; a retry after Slack failed posts it then, without a second notification in the
    bell. An automatic top-up that failed, paused or changes its price is emailed to the
    company's owners and admins too."""
    # With a `key`, its producer asking again is the same notification.
    key = data.get("key") or event_id

    if await notifications.add(key, data):
        try:
            await announce(data["recipient"], data["recipient_id"])
        except Exception:
            logger.exception("Couldn't announce a %s notification", data["kind"])

    await slack.deliver(data, key)
    await service_emails.billing_emails(data, key)


async def invite(data: dict, event_id: str) -> None:
    """A candidate who stopped the company's emails gets no invite, and the company sees it as
    undelivered, as with a bounce. Events saved before they carried the company's id are sent."""
    email = candidate_invite_email(data, settings.site_url, settings.email_link_secret)

    if data.get("company_id") and await opt_outs.opted_out(
        address_hash(data["email"]), data["company_id"]
    ):
        logger.info("Invite %s not sent: the candidate opted out", data.get("invite_id"))
        await report_undelivered(email.tags)

        return

    await deliver(email, event_id)


async def joined(data: dict, event_id: str) -> None:
    """Not to a candidate who stopped the company's emails."""
    if await opt_outs.opted_out(address_hash(data["email"]), data["company_id"]):
        logger.info("Link for %s not sent: the candidate opted out", data["invite_id"])

        return

    await deliver(
        candidate_joined_email(data, settings.site_url, settings.email_link_secret), event_id
    )


async def remind(data: dict, event_id: str) -> None:
    """No reminder to a candidate who stopped the company's emails or this invite's reminders;
    the invite itself reached them, so the company isn't told."""
    if data.get("company_id") and await opt_outs.opted_out(
        address_hash(data["email"]), data["company_id"], data.get("invite_id")
    ):
        logger.info("Reminder for %s not sent: the candidate opted out", data.get("invite_id"))

        return

    await deliver(
        candidate_reminder_email(data, settings.site_url, settings.email_link_secret), event_id
    )


async def handle(event_type: str, data: dict, event_id: str) -> None:
    """Sends the email or stores the notification an event asks for, and does a Resend web
    hook's work (each step safe to repeat); other events aren't ours."""
    if event_type == NOTIFICATION_REQUESTED:
        await notify(data, event_id)

    if event_type == EMAIL_WEBHOOK:
        await webhooks.handle(data["event"])

    if event_type == CANDIDATE_INVITED:
        await invite(data, event_id)

    if event_type == CANDIDATE_JOINED:
        await joined(data, event_id)

    if event_type == CANDIDATE_REMINDED:
        await remind(data, event_id)

    if event_type == MEMBER_INVITED:
        await deliver(member_invite_email(data, settings.site_url), event_id)

    if event_type == REPORT_SHARED:
        await deliver(report_email(data, settings.site_url), event_id)

    if event_type == COMPANY_DELETED:
        await notifications.remove_company(data["company_id"])
        await slack.disconnect(data["company_id"])
        await opt_outs.remove_company(data["company_id"])

    if event_type == CANDIDATE_REMOVED:
        await notifications.remove_candidate(data["email"], data["company_id"])

    if event_type == CANDIDATE_INTERVIEW_DELETED:
        await notifications.remove_interview_candidates(data["company_id"], data["interview_id"])

    if event_type == NEWS_DELETED:
        await notifications.remove_news(data["news_id"])

    if event_type == CONTACT_SENT:
        await deliver(contact_email(data, settings.contact_email), event_id)
