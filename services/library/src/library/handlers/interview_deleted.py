from prepza_common.events.deletions import InterviewDeleted

from library.services import sets


async def handle(event_id: str, data: dict) -> None:
    """Companies deleted an interview: its questions go, found by its set or its generation,
    with its bank opt-out; its questions' copies in the shared bank stay."""
    event = InterviewDeleted.model_validate(data)
    await sets.remove_interview(
        event.interview_id, event.company_id, event.set_id, event.generation_id
    )
