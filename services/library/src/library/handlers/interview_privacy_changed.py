from library.services import bank


async def handle(event_id: str, data: dict) -> None:
    """Companies kept an interview's questions out of the shared bank, or let them back in."""
    await bank.privacy_changed(data)
