from prepza_common.events.notes import NoteWritten

from notifications.services import notes


async def handle(data: dict, event_id: str) -> None:
    """An edited note: the digest shows its newest text."""
    await notes.written(NoteWritten.model_validate(data), created=False)
