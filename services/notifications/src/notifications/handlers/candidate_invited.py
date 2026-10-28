from notifications.services import events


async def handle(data: dict, event_id: str) -> None:
    """A candidate's invite email, unless they stopped the company's emails."""
    await events.invite(data, event_id)
