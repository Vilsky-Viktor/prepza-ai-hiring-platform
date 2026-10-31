from testee_common.events.notes import NoteWritten

from notifications.services import notes


async def handle(data: dict, event_id: str) -> None:
    """A member's new note: the other members' bells, the company's Slack channel and the digest
    hear of it, once (keyed by the note)."""
    await notes.written(NoteWritten.model_validate(data), created=True)
