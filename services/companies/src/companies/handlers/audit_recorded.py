from datetime import datetime

from companies.services import audit_events


async def handle(data: dict, event_id: str, at: datetime) -> None:
    """Another service's action goes into its company's log, once, at the time it happened."""
    await audit_events.record(event_id, data, at)
