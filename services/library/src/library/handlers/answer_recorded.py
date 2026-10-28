from library.services import answer_events


async def handle(event_id: str, data: dict) -> None:
    """A candidate's answer, added to its question's statistics."""
    await answer_events.record_answer(event_id, data)
