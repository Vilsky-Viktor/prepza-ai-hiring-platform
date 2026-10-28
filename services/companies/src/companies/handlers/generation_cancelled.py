from datetime import datetime

from companies.services import generation_events


async def handle(data: dict, event_id: str, at: datetime) -> None:
    """Generation cancelled an interview's topic review: the interview goes, and the company is told."""
    await generation_events.cancelled(data, event_id)
