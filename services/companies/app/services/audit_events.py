from datetime import datetime

from prepza_common.events.audit_actions import AUDIT_RECORDED

from app.storage import audit


async def handle(event_type: str, data: dict, event_id: str, at: datetime) -> None:
    """Stores another service's action in its company's log, once however often the event comes,
    at the time it happened (`at`, its outbox row's) however late it arrives; other events
    aren't ours."""
    if event_type != AUDIT_RECORDED:
        return

    await audit.store_event(event_id, data, at)
