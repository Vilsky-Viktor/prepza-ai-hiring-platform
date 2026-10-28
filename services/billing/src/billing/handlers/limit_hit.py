from datetime import datetime

from billing.services import usage


async def handle(data: dict, event_id: str, occurred_at: datetime) -> None:
    """A limit some service refused a call at, kept once by its event id."""
    await usage.record_hit(event_id, occurred_at, data)
