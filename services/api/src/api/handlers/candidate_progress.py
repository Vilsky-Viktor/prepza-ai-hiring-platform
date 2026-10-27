from datetime import datetime

from api.services import webhooks


async def handle(event_type: str, data: dict, event_id: str, occurred_at: datetime) -> None:
    """A candidate finished, started, wasn't reached or expired: the company's web hooks hear it,
    each once (its deliveries)."""
    await webhooks.candidate_event(event_type, data, event_id, occurred_at)
