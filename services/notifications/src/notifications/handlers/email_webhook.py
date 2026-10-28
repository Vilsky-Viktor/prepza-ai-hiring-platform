from notifications.services import webhooks


async def handle(data: dict, event_id: str) -> None:
    """A verified Resend web hook's work: suppression, telling companies and library."""
    await webhooks.handle(data["event"])
