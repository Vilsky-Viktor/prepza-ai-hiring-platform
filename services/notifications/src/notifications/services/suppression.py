# prepza's own suppression list: addresses that bounced for good, again and again for a while, or
# marked an email as spam, which every email skips (prepza's own inbox aside). Kept as hashes; a
# superadmin sees and removes one on an account's page.
import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from notifications.config import settings
from notifications.constants.bulk import SEND_TAG, SuppressionReason
from notifications.constants.suppression import (
    PERMANENT_BOUNCE,
    SOFT_BOUNCE_DAYS,
    SOFT_BOUNCES,
)
from notifications.constants.webhooks import (
    BOUNCED_EVENT,
    COMPLAINED_EVENT,
    ID_TAG,
    SUPPRESSED_EVENT,
)
from notifications.core.db import Session
from notifications.helpers.unsubscribe import address_hash
from notifications.integrations import resend
from notifications.repositories import bulk_recipients, soft_bounces, suppressed

logger = logging.getLogger(__name__)

REASONS = {
    BOUNCED_EVENT: SuppressionReason.BOUNCED,
    COMPLAINED_EVENT: SuppressionReason.COMPLAINED,
    SUPPRESSED_EVENT: SuppressionReason.SUPPRESSED,
}


async def from_webhook(event: dict) -> None:
    """A permanent bounce, a spam complaint or Resend's own suppression of any email (a
    candidate's invite too: an address that bounced or complained does so whichever company
    writes) suppresses its addresses, and so do SOFT_BOUNCES temporary bounces within
    SOFT_BOUNCE_DAYS; a complaint about a campaign counts against it, in the same save. Safe to
    repeat: Resend may send the web hook again."""
    reason = REASONS.get(event.get("type"))
    data = event.get("data") or {}
    tags = data.get("tags") or {}

    if reason is None:
        return

    if reason == SuppressionReason.BOUNCED and not permanent(data):
        await soft_bounced(data)

        return

    async with Session.begin() as session:
        for address in data.get("to") or []:
            await suppressed.add(session, address_hash(address), reason)

        if reason == SuppressionReason.COMPLAINED and tags.get(SEND_TAG) and tags.get(ID_TAG):
            await bulk_recipients.mark_complained(session, uuid.UUID(tags[SEND_TAG]), tags[ID_TAG])


def permanent(data: dict) -> bool:
    """Whether a bounce is for good (Resend's bounce type); one that doesn't say counts as one,
    as every bounce did before Resend reported its type."""
    kind = (data.get("bounce") or {}).get("type")

    return kind is None or kind == PERMANENT_BOUNCE


async def soft_bounced(data: dict) -> None:
    """Counts a temporary bounce once per email (Resend's id); the one that makes SOFT_BOUNCES
    within SOFT_BOUNCE_DAYS suppresses the address, in the same save."""
    since = datetime.now(UTC) - timedelta(days=SOFT_BOUNCE_DAYS)

    async with Session.begin() as session:
        for address in data.get("to") or []:
            hashed = address_hash(address)
            count = await soft_bounces.add(session, hashed, data.get("email_id") or "", since)

            if count >= SOFT_BOUNCES:
                await suppressed.add(session, hashed, SuppressionReason.SOFT_BOUNCED)


async def skipped(email: str) -> bool:
    """Whether the address is on the list, so nothing may be sent to it."""
    async with Session() as session:
        return await suppressed.get(session, address_hash(email)) is not None


async def lookup(email: str) -> dict | None:
    """Whether the address is suppressed: why and since when."""
    async with Session() as session:
        row = await suppressed.get(session, address_hash(email))

    return {"reason": row.reason, "created_at": row.created_at} if row else None


async def remove(email: str, superadmin_id: str) -> None:
    """Emails reach the address again: taken off Resend's own list first (when Resend sends),
    then off prepza's, so a failure leaves it on both and the superadmin tries again (502).
    Logged with its hash, never the address."""
    address = address_hash(email)

    if settings.resend_api_key:
        try:
            await resend.unsuppress(email)
        except Exception:
            logger.warning("Resend kept %s on its suppression list", address, exc_info=True)

            raise HTTPException(status.HTTP_502_BAD_GATEWAY) from None

    async with Session.begin() as session:
        await suppressed.remove(session, address)

    logger.warning("Superadmin %s removed %s from the suppression list", superadmin_id, address)
