from notifications.services import events


async def handle(data: dict, event_id: str) -> None:
    """The invite link for someone who started through a shareable link."""
    await events.joined(data, event_id)
