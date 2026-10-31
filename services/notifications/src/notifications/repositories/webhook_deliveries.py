import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events import outbox

from notifications.constants.events import EMAIL_WEBHOOK
from notifications.models.outbox import OutboxEvent


async def record(session: AsyncSession, delivery_id: str, event: dict) -> None:
    """A Resend web hook's event, saved as an email.webhook_received event whose id stands for
    its delivery (svix-id): Resend sending it again raises IntegrityError on the flush, and the
    one saved first stays."""
    event_id = uuid.uuid5(uuid.NAMESPACE_URL, f"resend:{delivery_id}")
    outbox.add(session, OutboxEvent, EMAIL_WEBHOOK, {"event": event}, event_id)
    await session.flush()
