import logging

from fastapi import status
from prepza_common import http
from prepza_common.http import bearer
from prepza_common.limits import record_hit

from app.config.settings import settings
from app.constants.email import (
    RESEND_ALREADY_SENT,
    RESEND_EMAILS_URL,
    RESEND_IN_PROGRESS,
    RESEND_QUOTA_ERRORS,
    RESEND_REFUSED,
    SEND_TIMEOUT_S,
)
from app.models.email import Email

logger = logging.getLogger(__name__)


class EmailRefused(Exception):
    """Resend won't ever send this email; retrying is pointless."""


class ResendBusy(Exception):
    """Over Resend's per-second limit (a burst of invites) or its quota, or the same
    email still being sent by another try: nothing was sent yet, a retry will."""


def error_name(response) -> str | None:
    """The name of Resend's error (its JSON body's "name"), when it gives one."""
    try:
        body = response.json()
    except ValueError:
        return None

    return body.get("name") if isinstance(body, dict) else None


def quota_used(response) -> bool:
    """Whether Resend's 429 is for its daily or monthly quota rather than its per-second limit:
    its error's name says so."""
    return error_name(response) in RESEND_QUOTA_ERRORS


async def send(email: Email, idempotency_key: str) -> None:
    """Sends through Resend, on the service's shared connections; the same key within 24 hours
    never sends twice, so retries are safe. A key Resend already sent with (a retry whose email
    changed meanwhile, say its language) counts as sent."""
    response = await http.get_client().post(
        RESEND_EMAILS_URL,
        headers={**bearer(settings.resend_api_key), "Idempotency-Key": idempotency_key},
        json={
            "from": settings.mail_from_updates if email.optional else settings.mail_from,
            "to": [email.to],
            "subject": email.subject,
            "html": email.html,
            "text": email.text,
            "tags": [{"name": name, "value": value} for name, value in email.tags.items()],
            "reply_to": email.reply_to or settings.contact_email,
            "headers": email.headers,
            **(
                {
                    "attachments": [
                        {"filename": name, "content": content}
                        for name, content in email.attachments
                    ]
                }
                if email.attachments
                else {}
            ),
        },
        timeout=SEND_TIMEOUT_S,
    )

    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        name = "RESEND_DAILY_QUOTA" if quota_used(response) else "RESEND_RATE_LIMIT"
        await record_hit(name, kind="provider:resend", scope="everyone")

        raise ResendBusy()

    if response.status_code == status.HTTP_409_CONFLICT:
        name = error_name(response)

        if name == RESEND_ALREADY_SENT:
            logger.info("Resend already sent the email for key %s", idempotency_key)

            return

        if name == RESEND_IN_PROGRESS:
            raise ResendBusy()

    if response.status_code in RESEND_REFUSED:
        raise EmailRefused(f"Resend refused the email ({response.status_code}): {response.text}")

    if response.is_error:
        raise RuntimeError(f"Resend refused the email ({response.status_code}): {response.text}")
