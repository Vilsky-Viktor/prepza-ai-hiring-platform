from testee_common.events import outbox

from accounts.core.db import Session
from accounts.models.outbox import OutboxEvent


async def flush() -> int:
    return await outbox.flush(Session, OutboxEvent)


async def flush_quietly() -> None:
    await outbox.flush_quietly(Session, OutboxEvent)
