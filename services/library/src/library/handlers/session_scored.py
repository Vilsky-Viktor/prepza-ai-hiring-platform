from library.services import answer_events


async def handle(event_id: str, data: dict) -> None:
    """A finished topic's results, added to its questions' statistics."""
    await answer_events.record_results(event_id, data)
