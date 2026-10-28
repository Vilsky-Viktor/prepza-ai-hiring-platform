from datetime import datetime

from companies.services import generation_events


async def handle(data: dict, event_id: str, at: datetime) -> None:
    """An interview's questions are ready: stored on it, and the company told once."""
    await generation_events.completed(data, event_id)
