# prepza's own suppression list: addresses that bounced for good, again and again for a while, or
# marked an email as spam, which bulk sends skip. Kept as hashes; a superadmin sees and removes one on an account's page.
import logging
import uuid
from datetime import UTC, datetime, timedelta

from app.constants.bulk import SEND_TAG, SuppressionReason
from app.constants.suppression import PERMANENT_BOUNCE, SOFT_BOUNCE_DAYS, SOFT_BOUNCES
from app.constants.webhooks import (
    BOUNCED_EVENT,
    CANDIDATE_INVITE_KIND,
    COMPLAINED_EVENT,
    ID_TAG,
    KIND_TAG,
    SUPPRESSED_EVENT,
)
from app.helpers.unsubscribe import address_hash
from app.storage import bulk_recipients, soft_bounces, suppressed

logger = logging.getLogger(__name__)

REASONS = {
    BOUNCED_EVENT: SuppressionReason.BOUNCED,
    COMPLAINED_EVENT: SuppressionReason.COMPLAINED,
    SUPPRESSED_EVENT: SuppressionReason.SUPPRESSED,
}


async def from_webhook(event: dict) -> None:
    """A permanent bounce, a spam complaint or Resend's own suppression of an email to a member
    (not a candidate's invite, which is a company's) suppresses its addresses, and so do
    SOFT_BOUNCES temporary bounces within SOFT_BOUNCE_DAYS; a complaint about a campaign counts
    against it. Safe to repeat: Resend may send the web hook again."""
    reason = REASONS.get(event.get("type"))
    data = event.get("data") or {}
    tags = data.get("tags") or {}

    if reason is None or tags.get(KIND_TAG) == CANDIDATE_INVITE_KIND:
        return

    if reason == SuppressionReason.BOUNCED and not permanent(data):
        await soft_bounced(data)

        return

    for address in data.get("to") or []:
        await suppressed.add(address_hash(address), reason)

    if reason == SuppressionReason.COMPLAINED and tags.get(SEND_TAG) and tags.get(ID_TAG):
        await bulk_recipients.mark_complained(uuid.UUID(tags[SEND_TAG]), tags[ID_TAG])


def permanent(data: dict) -> bool:
    """Whether a bounce is for good (Resend's bounce type); one that doesn't say counts as one,
    as every bounce did before Resend reported its type."""
    kind = (data.get("bounce") or {}).get("type")

    return kind is None or kind == PERMANENT_BOUNCE


async def soft_bounced(data: dict) -> None:
    """Counts a temporary bounce once per email (Resend's id); the one that makes SOFT_BOUNCES
    within SOFT_BOUNCE_DAYS suppresses the address."""
    since = datetime.now(UTC) - timedelta(days=SOFT_BOUNCE_DAYS)

    for address in data.get("to") or []:
        hashed = address_hash(address)

        if await soft_bounces.add(hashed, data.get("email_id") or "", since) >= SOFT_BOUNCES:
            await suppressed.add(hashed, SuppressionReason.SOFT_BOUNCED)


async def lookup(email: str) -> dict | None:
    """Whether the address is suppressed: why and since when."""
    row = await suppressed.get(address_hash(email))

    return {"reason": row.reason, "created_at": row.created_at} if row else None


async def remove(email: str, superadmin_id: str) -> None:
    """Bulk sends reach the address again; logged with its hash, never the address."""
    address = address_hash(email)
    await suppressed.remove(address)
    logger.warning("Superadmin %s removed %s from the suppression list", superadmin_id, address)
