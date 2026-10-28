from datetime import datetime

from companies.repositories import audit


async def record(event_id: str, data: dict, at: datetime) -> None:
    """Stores another service's action in its company's log, once however often the event comes,
    at the time it happened (`at`, its outbox row's) however late it arrives."""
    await audit.store_event(event_id, data, at)
