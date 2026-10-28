import logging

from prepza_common.http.pacing import wait_turn

from notifications.config import settings
from notifications.constants.email import RESEND_PACE_KEY, RESEND_PER_SECOND
from notifications.integrations import resend, smtp
from notifications.integrations.redis import get_redis
from notifications.models.email import Email
from notifications.services import suppression
from notifications.services.webhooks import report_undelivered

logger = logging.getLogger(__name__)


async def transmit(email: Email, idempotency_key: str) -> None:
    """Through Resend when it's set up, paced under its per-second limit, else to the SMTP
    server (Mailpit). Every instance and run takes turns from one RESEND_PER_SECOND, counted in
    Redis (unpaced with Redis down: a 429 is still retried). Resend never sends the same key
    twice within 24 hours, so a retry is safe.
    Raises resend.ResendBusy over its per-second limit, resend.EmailRefused when it won't ever
    send it, and on any failure a retry may fix."""
    if settings.resend_api_key:
        await wait_turn(get_redis(), RESEND_PACE_KEY, RESEND_PER_SECOND)
        await resend.send(email, idempotency_key)

        return

    await smtp.send(email)


async def send(email: Email, idempotency_key: str) -> None:
    """As transmit, but nothing goes to an address on prepza's suppression list (prepza's own
    inbox aside: the contact page's messages), and an email Resend refuses for good isn't
    retried. Either way, like a bounce, an invite shows as undelivered, and any other email is
    logged."""
    if email.to != settings.contact_email and await suppression.skipped(email.to):
        logger.info("Email for %s not sent: the address is suppressed", email.tags or "untagged")
        await report_undelivered(email.tags)

        return

    try:
        await transmit(email, idempotency_key)
    except resend.EmailRefused:
        # Final, like a bounce: not retried. An invite shows as undelivered; any other email
        # (a report, a contact message, a digest) would be lost unseen, so it's an error.
        if email.tags:
            logger.warning("Email for %s refused", email.tags, exc_info=True)
        else:
            logger.exception("An untagged email was refused")

        await report_undelivered(email.tags)
