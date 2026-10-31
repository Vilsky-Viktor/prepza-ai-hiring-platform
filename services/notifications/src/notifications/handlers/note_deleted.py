from testee_common.events.notes import NoteDeleted

from notifications.services import notes


async def handle(data: dict, event_id: str) -> None:
    """A deleted note leaves the bell and the digest, and a late event about it tells nobody."""
    await notes.deleted(NoteDeleted.model_validate(data))
