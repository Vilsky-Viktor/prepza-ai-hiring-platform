from prepza_common.events import outbox

from app.models.outbox import OutboxEvent
from app.storage.db import Session


async def flush() -> int:
    return await outbox.flush(Session, OutboxEvent)


async def flush_quietly() -> None:
    await outbox.flush_quietly(Session, OutboxEvent)
