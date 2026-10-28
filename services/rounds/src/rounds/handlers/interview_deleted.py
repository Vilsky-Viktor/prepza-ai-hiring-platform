from prepza_common.events.deletions import InterviewDeleted

from rounds.services import session_removal


async def handle(data: dict) -> None:
    """Companies deleted an interview: its candidates' and previews' sessions go, with their
    answers and signals. One deleted while still generating has no set, so no sessions."""
    event = InterviewDeleted.model_validate(data)

    if event.set_id is not None:
        await session_removal.remove_interview(event.set_id)
