import uuid

from prepza_common import outbox
from sqlalchemy.exc import IntegrityError

from app.constants.events import EMAIL_WEBHOOK
from app.models.outbox import OutboxEvent
from app.storage.db import Session


async def record(delivery_id: str, event: dict) -> bool:
    """A Resend web hook's event, saved as an email.webhook_received event whose id stands for
    its delivery (svix-id): Resend sending it again keeps the one saved. Whether it's new."""
    event_id = uuid.uuid5(uuid.NAMESPACE_URL, f"resend:{delivery_id}")

    try:
        async with Session() as session:
            outbox.add(session, OutboxEvent, EMAIL_WEBHOOK, {"event": event}, event_id)
            await session.commit()
    except IntegrityError:
        return False

    return True
