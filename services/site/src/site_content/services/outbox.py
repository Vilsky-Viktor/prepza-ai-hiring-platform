from testee_common.events import outbox

from site_content.core.db import Session
from site_content.models.outbox import OutboxEvent


async def flush() -> int:
    return await outbox.flush(Session, OutboxEvent)


async def flush_quietly() -> None:
    await outbox.flush_quietly(Session, OutboxEvent)
