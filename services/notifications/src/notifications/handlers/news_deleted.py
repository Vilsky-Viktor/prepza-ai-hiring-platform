from notifications.repositories import notifications


async def handle(data: dict, event_id: str) -> None:
    """A deleted news post's notification for everyone goes."""
    await notifications.remove_news(data["news_id"])
