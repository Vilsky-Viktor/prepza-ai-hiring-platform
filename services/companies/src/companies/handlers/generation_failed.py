from datetime import datetime

from companies.services import generation_events


async def handle(data: dict, event_id: str, at: datetime) -> None:
    """An interview's generation failed: the interview shows it until a retry."""
    await generation_events.failed(data, event_id)
