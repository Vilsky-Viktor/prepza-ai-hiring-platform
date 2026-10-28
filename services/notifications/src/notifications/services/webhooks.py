import logging

from sqlalchemy.exc import IntegrityError

from notifications.constants.unsubscribe import USER_SETTINGS
from notifications.constants.webhooks import (
    CANDIDATE_KINDS,
    CANDIDATE_REMINDER_KIND,
    COMPANY_TAG,
    COMPLAINED_EVENT,
    ID_TAG,
    KIND_TAG,
    UNDELIVERED_EVENTS,
)
from notifications.core.db import Session
from notifications.helpers.unsubscribe import address_hash
from notifications.integrations import companies
from notifications.repositories import opt_outs, webhook_deliveries
from notifications.services import outbox as outbox_service
from notifications.services.suppression import from_webhook
from notifications.services.unsubscribe import apply

logger = logging.getLogger(__name__)


async def record(delivery_id: str, event: dict) -> None:
    """A Resend web hook's event, saved as an email.webhook_received event whose id stands for
    its delivery (svix-id), so Resend sending it again keeps the one saved; then published."""
    try:
        async with Session.begin() as session:
            await webhook_deliveries.record(session, delivery_id, event)
    except IntegrityError:
        pass

    await outbox_service.flush_quietly()


async def handle(event: dict) -> None:
    """Tells the invite's owner its email wasn't delivered, turns off an optional email the user
    marked as spam, and keeps a member's address that bounced or complained off bulk sends;
    other events and untagged emails aren't ours to act on."""
    if event.get("type") not in UNDELIVERED_EVENTS:
        return

    tags = (event.get("data") or {}).get("tags") or {}
    # Counted for the bounce alert (infra/terraform/monitoring_logs.tf); no address, only its kind.
    logger.info("Email not delivered (%s): %s", event["type"], tags.get(KIND_TAG, "untagged"))

    await from_webhook(event)

    if event["type"] == COMPLAINED_EVENT:
        await complained(tags, (event.get("data") or {}).get("to") or [])

    await report_undelivered(tags)


async def complained(tags: dict[str, str], addresses: list[str]) -> None:
    """A spam complaint about an optional email turns it off, as its unsubscribe link would: a
    user's digest or reminders (logged in library as an unsubscribe), or a candidate's
    reminders for that invite. Safe to repeat when Resend sends the webhook again."""
    kind, about = tags.get(KIND_TAG), tags.get(ID_TAG)

    if kind in USER_SETTINGS and about:
        await apply({"type": kind, "user_id": about})

    if kind == CANDIDATE_REMINDER_KIND and about and tags.get(COMPANY_TAG):
        async with Session.begin() as session:
            for address in addresses:
                await opt_outs.add(session, address_hash(address), tags[COMPANY_TAG], about)


async def report_undelivered(tags: dict[str, str]) -> None:
    """Marks the invite the email was for as undelivered, from its tags."""
    kind, invite_id = tags.get(KIND_TAG), tags.get(ID_TAG)

    if not invite_id:
        return

    if kind in CANDIDATE_KINDS:
        await companies.invite_undelivered(invite_id)
