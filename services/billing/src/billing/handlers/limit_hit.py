from datetime import datetime

from billing.repositories import usage


async def handle(data: dict, event_id: str, occurred_at: datetime) -> None:
    """A limit some service refused a call at, kept once by its event id."""
    await usage.store_hit(event_id, occurred_at, data)
