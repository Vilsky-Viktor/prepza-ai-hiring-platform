from notifications.services import events


async def handle(data: dict, event_id: str) -> None:
    """A notification for the bell (and Slack, and billing's emails), stored once per key."""
    await events.notify(data, event_id)
