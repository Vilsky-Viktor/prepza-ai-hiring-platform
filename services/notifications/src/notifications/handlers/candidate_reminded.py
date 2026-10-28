from notifications.services import events


async def handle(data: dict, event_id: str) -> None:
    """A reminder to a candidate who hasn't started."""
    await events.remind(data, event_id)
